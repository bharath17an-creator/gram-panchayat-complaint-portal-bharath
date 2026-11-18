import sqlite3
from pathlib import Path


# Project folder
BASE_DIR = Path(__file__).resolve().parent

# Database folder
DATABASE_DIR = BASE_DIR / "database"

# Create database folder if it does not exist
DATABASE_DIR.mkdir(exist_ok=True)

# Database file
DATABASE_PATH = DATABASE_DIR / "complaints.db"


# Connect to SQLite database
connection = sqlite3.connect(DATABASE_PATH)

cursor = connection.cursor()


# ============================================================
# USERS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")


# ============================================================
# DEPARTMENTS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")


# ============================================================
# COMPLAINTS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    complaint_number TEXT UNIQUE NOT NULL,

    citizen_id INTEGER NOT NULL,

    category TEXT NOT NULL,

    title TEXT NOT NULL,

    description TEXT NOT NULL,

    location TEXT NOT NULL,

    landmark TEXT,

    latitude REAL,

    longitude REAL,

    image_filename TEXT,

    status TEXT NOT NULL DEFAULT 'Submitted',

    priority TEXT NOT NULL DEFAULT 'Normal',

    department_id INTEGER,

    assigned_staff_id INTEGER,

    resolution_notes TEXT,

    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved_at TEXT,

    closed_at TEXT,

    FOREIGN KEY (citizen_id) REFERENCES users(id),

    FOREIGN KEY (department_id) REFERENCES departments(id),

    FOREIGN KEY (assigned_staff_id) REFERENCES users(id)
)
""")


# ============================================================
# COMPLAINT STATUS HISTORY TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaint_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    complaint_id INTEGER NOT NULL,

    old_status TEXT,

    new_status TEXT NOT NULL,

    changed_by INTEGER,

    remarks TEXT,

    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id) REFERENCES complaints(id),

    FOREIGN KEY (changed_by) REFERENCES users(id)
)
""")


# ============================================================
# FEEDBACK TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    complaint_id INTEGER UNIQUE NOT NULL,

    citizen_id INTEGER NOT NULL,

    rating INTEGER NOT NULL,

    comments TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id) REFERENCES complaints(id),

    FOREIGN KEY (citizen_id) REFERENCES users(id)
)
""")


# ============================================================
# INSERT DEFAULT DEPARTMENTS
# ============================================================

departments = [
    (
        "Roads and Infrastructure",
        "Roads, potholes, footpaths and related infrastructure"
    ),
    (
        "Water Supply",
        "Drinking water and water supply related complaints"
    ),
    (
        "Street Lighting",
        "Street lights and public lighting"
    ),
    (
        "Sanitation and Waste",
        "Waste management, drainage and sanitation"
    ),
    (
        "Public Health",
        "Public health and hygiene related complaints"
    ),
    (
        "General Administration",
        "Other civic and administrative complaints"
    )
]


cursor.executemany("""
INSERT OR IGNORE INTO departments (name, description)
VALUES (?, ?)
""", departments)


# Save changes
connection.commit()


# Close database
connection.close()


print()
print("==============================================")
print("DATABASE INITIALIZATION SUCCESSFUL")
print("==============================================")
print(f"Database created at:")
print(DATABASE_PATH)
print()
print("Tables created:")
print("1. users")
print("2. departments")
print("3. complaints")
print("4. complaint_status_history")
print("5. feedback")
print()
print("Default departments added.")
print("==============================================")