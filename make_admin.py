
import os
from database import get_db_connection
from werkzeug.security import generate_password_hash

name = os.environ.get("ADMIN_NAME")
email = os.environ.get("ADMIN_EMAIL")
phone = os.environ.get("ADMIN_PHONE", "9999999999")
password = os.environ.get("ADMIN_PASSWORD")

if not all([name, email, password]):
    raise ValueError("Set ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD in Render.")

conn = get_db_connection()

try:
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:
        print("Admin account already exists.")
    else:
        conn.execute(
            """
            INSERT INTO users
            (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                phone,
                generate_password_hash(password),
                "admin"
            )
        )
        conn.commit()
        print("SUCCESS: Admin account created.")

finally:
    conn.close()
