import sqlite3
from pathlib import Path


# Get the main project folder
BASE_DIR = Path(__file__).resolve().parent

# Location of the SQLite database
DATABASE_PATH = BASE_DIR / "database" / "complaints.db"


def get_db_connection():
    """
    Create and return a connection to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Allows us to access database columns by name
    connection.row_factory = sqlite3.Row

    # Enforce foreign-key relationships
    connection.execute("PRAGMA foreign_keys = ON")

    return connection