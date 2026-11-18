
import sqlite3
from pathlib import Path


# Get the main project folder
BASE_DIR = Path(__file__).resolve().parent

# Set the database folder and file location
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "complaints.db"


def get_db_connection():
    """
    Create and return a connection to the SQLite database.
    """

    # Create the database folder if it does not exist
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to the database
    connection = sqlite3.connect(str(DATABASE_PATH))

    # Access database columns using their names
    connection.row_factory = sqlite3.Row

    # Enable foreign key relationships
    connection.execute("PRAGMA foreign_keys = ON")

    return connection
