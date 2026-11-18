from database import get_db_connection

conn = get_db_connection()

try:
    # Add new columns to the complaints table
    conn.execute("ALTER TABLE complaints ADD COLUMN feedback_rating INTEGER;")
    conn.execute("ALTER TABLE complaints ADD COLUMN feedback_text TEXT;")
    print("SUCCESS: Database upgraded to support Feedback and Ratings!")
except Exception as e:
    print("Notice (The database might already be upgraded):", e)

conn.commit()
conn.close()