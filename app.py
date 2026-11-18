from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

# Secret key used to protect login sessions and flash messages
app.secret_key = "change-this-secret-key-later"



# ============================================================
# MULTILANGUAGE SUPPORT (English, Kannada and Hindi)
# ============================================================
from urllib.parse import urlparse
from translations import TRANSLATIONS

SUPPORTED_LANGUAGES = {
    "en": "English",
    "kn": "ಕನ್ನಡ",
    "hi": "हिन्दी",
}

def translate_ui(text):
    """Return the selected-language UI label, falling back to English."""
    language = session.get("language", "en")
    return TRANSLATIONS.get(language, {}).get(text, text)

@app.context_processor
def inject_language_helpers():
    return {
        "_": translate_ui,
        "supported_languages": SUPPORTED_LANGUAGES,
        "current_language": session.get("language", "en"),
    }

@app.route("/set-language", methods=["POST"])
def set_language():
    """Save the visitor's language choice in their Flask session."""
    language = request.form.get("language", "en")
    if language in SUPPORTED_LANGUAGES:
        session["language"] = language

    next_url = request.form.get("next", "/")
    parsed = urlparse(next_url)

    # Only allow a local path to prevent external redirect abuse.
    if parsed.netloc or not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/"

    return redirect(next_url)


# ============================================================
# TIME FORMATTER
# ============================================================

def format_indian_time(timestamp):
    if not timestamp:
        return ""
    try:
        utc_time = datetime.strptime(
            timestamp,
            "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        indian_time = utc_time.astimezone(
            ZoneInfo("Asia/Kolkata")
        )

        return indian_time.strftime(
            "%d %B %Y, %I:%M:%S %p"
        )
    except Exception:
        return timestamp


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# CITIZEN REGISTRATION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users
                (full_name, email, phone, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, email, phone, password_hash, "citizen")
            )
            connection.commit()
        except Exception:
            connection.close()
            flash("Registration failed. That email or phone number may already be registered.", "danger")
            return redirect(url_for("register"))

        connection.close()
        flash("Registration successful! Please log in to your account.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND is_active = 1
            """,
            (email,)
        ).fetchone()
        connection.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for("login"))

        # Store user information in the login session
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["user_role"] = user["role"]

        flash(f"Welcome back, {user['full_name']}!", "success")

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
            
        if user["role"] == "staff":
            return redirect(url_for("staff_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

@app.route("/submit-complaint", methods=["GET", "POST"])
def submit_complaint():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form["category"].strip()
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()
        landmark = request.form["landmark"].strip()

        # Receive GPS coordinates from the complaint form.
        # If the citizen does not allow GPS, save NULL values.
        latitude = request.form.get("latitude") or None
        longitude = request.form.get("longitude") or None

        # Check that the received coordinates are valid.
        try:
            if latitude is not None and longitude is not None:
                latitude = float(latitude)
                longitude = float(longitude)

                if not (-90 <= latitude <= 90):
                    raise ValueError("Invalid latitude")

                if not (-180 <= longitude <= 180):
                    raise ValueError("Invalid longitude")
            else:
                latitude = None
                longitude = None

        except (ValueError, TypeError):
            flash(
                "Invalid GPS coordinates. Please detect your location again.",
                "danger"
            )
            return redirect(url_for("submit_complaint"))

        complaint_number = "GP-" + str(
            __import__("uuid").uuid4()
        ).split("-")[0].upper()

        connection = get_db_connection()

        cursor = connection.execute(
            """
            INSERT INTO complaints
            (
                complaint_number,
                citizen_id,
                category,
                title,
                description,
                location,
                landmark,
                latitude,
                longitude,
                status,
                priority
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                complaint_number,
                session["user_id"],
                category,
                title,
                description,
                location,
                landmark,
                latitude,
                longitude,
                "Submitted",
                "Normal"
            )
        )

        complaint_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO complaint_status_history
            (complaint_id, old_status, new_status, changed_by, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            (complaint_id, None, "Submitted", session["user_id"], "Complaint submitted by citizen")
        )

        connection.commit()
        connection.close()

        flash(f"Complaint Submitted Successfully! Your Tracking Number is: {complaint_number}", "success")
        return redirect(url_for("dashboard"))

    return render_template("submit_complaint.html")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("user_role") != "admin":
        return "Unauthorized access. Admins only.", 403

    connection = get_db_connection()

    total_complaints = connection.execute("SELECT COUNT(*) AS total FROM complaints").fetchone()["total"]
    submitted_complaints = connection.execute("SELECT COUNT(*) AS total FROM complaints WHERE status = 'Submitted'").fetchone()["total"]
    in_progress_complaints = connection.execute("SELECT COUNT(*) AS total FROM complaints WHERE status = 'In Progress'").fetchone()["total"]
    resolved_complaints = connection.execute("SELECT COUNT(*) AS total FROM complaints WHERE status = 'Resolved'").fetchone()["total"]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        user_name=session["user_name"],
        total_complaints=total_complaints,
        submitted_complaints=submitted_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints
    )


# ============================================================
# ADMIN COMPLAINT MANAGEMENT
# ============================================================

@app.route("/admin/complaints")
def admin_complaints():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    if session.get("user_role") != "admin":
        return "Unauthorized access. Admins only.", 403
        
    connection = get_db_connection()
    
    complaints = connection.execute("""
        SELECT
            complaints.complaint_number, complaints.category, complaints.title,
            complaints.status, complaints.priority, complaints.submitted_at,
            users.full_name AS citizen_name
        FROM complaints
        JOIN users ON complaints.citizen_id = users.id
        ORDER BY complaints.id DESC
    """).fetchall()
    
    connection.close()
    
    formatted_complaints = []
    for complaint in complaints:
        complaint = dict(complaint)
        complaint["submitted_at"] = format_indian_time(complaint["submitted_at"])
        formatted_complaints.append(complaint)
        
    return render_template("admin_complaints.html", complaints=formatted_complaints)


# ============================================================
# ADMIN COMPLAINT DETAIL
# ============================================================

@app.route("/admin/complaint/<string:complaint_number>", methods=["GET", "POST"])
def admin_complaint_detail(complaint_number):
    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect(url_for("login"))

    connection = get_db_connection()
    
    complaint = connection.execute(
        "SELECT * FROM complaints WHERE complaint_number = ?", 
        (complaint_number,)
    ).fetchone()

    if complaint is None:
        connection.close()
        return redirect(url_for("admin_complaints"))

    if request.method == "POST":
        new_status = request.form["status"]
        admin_remark = request.form["admin_remark"]
        old_status = complaint["status"]

        connection.execute(
            "UPDATE complaints SET status = ? WHERE complaint_number = ?",
            (new_status, complaint_number)
        )
        
        connection.execute(
            """
            INSERT INTO complaint_status_history 
            (complaint_id, old_status, new_status, changed_by, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            (complaint["id"], old_status, new_status, session["user_id"], admin_remark)
        )
        connection.commit()
        connection.close()
        
        flash(f"Complaint {complaint_number} updated to '{new_status}'.", "success")
        return redirect(url_for("admin_complaint_detail", complaint_number=complaint_number))

    connection.close()
    return render_template("admin_complaint_detail.html", complaint=complaint)


# ============================================================
# CITIZEN DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user_name=session["user_name"])


# ============================================================
# MY COMPLAINTS
# ============================================================

@app.route("/my-complaints")
def my_complaints():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    complaints = connection.execute(
        """
        SELECT complaint_number, category, title, status, submitted_at
        FROM complaints
        WHERE citizen_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()
    return render_template("my_complaints.html", complaints=complaints)


# ============================================================
# TRACK COMPLAINT
# ============================================================

@app.route("/track", methods=["GET", "POST"])
def track():
    if "user_id" not in session:
        return redirect(url_for("login"))

    complaint = None
    status_history = []
    searched = False

    if request.method == "POST":
        complaint_number = request.form["complaint_number"].strip()

        connection = get_db_connection()

        complaint = connection.execute(
            """
            SELECT id, complaint_number, category, title, status, submitted_at, feedback_rating, feedback_text
            FROM complaints
            WHERE complaint_number = ? AND citizen_id = ?
            """,
            (complaint_number, session["user_id"])
        ).fetchone()

        if complaint:
            history_rows = connection.execute(
                """
                SELECT old_status, new_status, remarks, changed_at
                FROM complaint_status_history
                WHERE complaint_id = ?
                ORDER BY id ASC
                """,
                (complaint["id"],)
            ).fetchall()

            complaint = dict(complaint)
            complaint["submitted_at"] = format_indian_time(complaint["submitted_at"])

            status_history = []
            for history in history_rows:
                history = dict(history)
                history["changed_at"] = format_indian_time(history["changed_at"])
                status_history.append(history)

        connection.close()
        searched = True

    return render_template(
        "track.html",
        complaint=complaint,
        status_history=status_history,
        searched=searched
    )


# ============================================================
# CITIZEN FEEDBACK & REOPEN
# ============================================================

@app.route("/feedback/<string:complaint_number>", methods=["POST"])
def submit_feedback(complaint_number):
    if "user_id" not in session:
        return redirect(url_for("login"))

    action = request.form.get("action")
    
    connection = get_db_connection()
    complaint = connection.execute(
        "SELECT id, status FROM complaints WHERE complaint_number = ? AND citizen_id = ?", 
        (complaint_number, session["user_id"])
    ).fetchone()

    if complaint and complaint["status"] == "Resolved":
        
        if action == "reopen":
            connection.execute(
                "UPDATE complaints SET status = 'In Progress' WHERE id = ?",
                (complaint["id"],)
            )
            connection.execute(
                """
                INSERT INTO complaint_status_history 
                (complaint_id, old_status, new_status, changed_by, remarks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (complaint["id"], "Resolved", "In Progress", session["user_id"], "Citizen reopened the complaint: Issue not resolved.")
            )
            flash(f"Complaint {complaint_number} has been reopened and sent back to staff.", "warning")
            
        elif action == "rate":
            rating = request.form.get("rating")
            feedback_text = request.form.get("feedback_text")
            
            connection.execute(
                "UPDATE complaints SET feedback_rating = ?, feedback_text = ? WHERE id = ?",
                (rating, feedback_text, complaint["id"])
            )
            connection.execute(
                """
                INSERT INTO complaint_status_history 
                (complaint_id, old_status, new_status, changed_by, remarks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (complaint["id"], "Resolved", "Resolved", session["user_id"], f"Citizen Rating: {rating} Stars. Feedback: {feedback_text}")
            )
            flash("Thank you! Your feedback and star rating have been saved.", "success")
        
        connection.commit()

    connection.close()
    return redirect(url_for("my_complaints"))


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/staff")
def staff_dashboard():
    if "user_id" not in session or session.get("user_role") != "staff":
        return redirect(url_for("login"))

    connection = get_db_connection()
    
    complaints = connection.execute(
        """
        SELECT complaint_number, category, title, status, priority, submitted_at, description, location
        FROM complaints 
        WHERE status IN ('Assigned', 'In Progress')
        ORDER BY priority DESC, id DESC
        """
    ).fetchall()
    
    formatted_complaints = []
    for complaint in complaints:
        complaint = dict(complaint)
        complaint["submitted_at"] = format_indian_time(complaint["submitted_at"])
        formatted_complaints.append(complaint)

    connection.close()
    
    return render_template("staff_dashboard.html", user_name=session.get("user_name"), complaints=formatted_complaints)


# ============================================================
# STAFF UPDATE COMPLAINT
# ============================================================

@app.route("/staff/update/<string:complaint_number>", methods=["POST"])
def staff_update_complaint(complaint_number):
    if "user_id" not in session or session.get("user_role") != "staff":
        return redirect(url_for("login"))

    new_status = request.form.get("status")
    staff_remark = request.form.get("staff_remark")

    connection = get_db_connection()
    complaint = connection.execute(
        "SELECT id, status FROM complaints WHERE complaint_number = ?", 
        (complaint_number,)
    ).fetchone()

    if complaint:
        old_status = complaint["status"]
        
        connection.execute(
            "UPDATE complaints SET status = ? WHERE complaint_number = ?",
            (new_status, complaint_number)
        )
        
        connection.execute(
            """
            INSERT INTO complaint_status_history 
            (complaint_id, old_status, new_status, changed_by, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            (complaint["id"], old_status, new_status, session["user_id"], "Staff Update: " + staff_remark)
        )
        connection.commit()
        flash(f"Task {complaint_number} updated to '{new_status}'.", "success")

    connection.close()
    return redirect(url_for("staff_dashboard"))


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("login"))


# ============================================================
# ERROR HANDLING (404 & 500)
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)