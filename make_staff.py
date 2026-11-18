from database import get_db_connection
from werkzeug.security import generate_password_hash

conn = get_db_connection()
password = generate_password_hash("staff123")

try:
    conn.execute(
        """
        INSERT INTO users (full_name, email, phone, password_hash, role) 
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Electrician Ravi", "staff@gmail.com", "9999999999", password, "staff")
    )
    conn.commit()
    print("SUCCESS: Staff account created! Email: staff@gmail.com | Password: staff123")
except Exception as e:
    print("Notice: Account might already exist or there was an error:", e)

conn.close()