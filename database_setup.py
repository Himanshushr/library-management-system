# database_setup.py
import sqlite3
import datetime

DB_NAME = 'library.db'

def initialize_database():
    """Connects to the database and creates the necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- 1. Users/Membership Table ---
    # Stores member information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            membership_type TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
    """)

    # --- 2. Books/Inventory Table ---
    # Stores book details and availability
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            serial_no TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
    """)

    # --- 3. Transactions/Issue & Return Table ---
    # Stores records of all loans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no TEXT NOT NULL,
            user_id TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            fine_amount REAL DEFAULT 0.0,
            is_returned INTEGER DEFAULT 0, -- 0 for outstanding, 1 for returned
            FOREIGN KEY (serial_no) REFERENCES books(serial_no),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    print("Database structure initialized successfully.")

def seed_data():
    """Inserts mock data into the tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.date.today().isoformat()
    future_date_year = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    future_date_half = (datetime.date.today() + datetime.timedelta(days=180)).isoformat()

    # 1. Seed Users
    users_data = [
        ('U101', 'Alice Cooper', '1 year', future_date_year),
        ('U102', 'Bob Dylan', '6 months', future_date_half),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", users_data)
    
    # 2. Seed Books
    books_data = [
        ('SN-4521', 'The Lion\'s Roar', 'A. B. Smith', 2, 2),
        ('SN-1001', 'History of Python', 'G. van Rossum', 1, 1),
        ('SN-9876', 'Movie Title X', 'N/A', 0, 0),
    ]
    cursor.executemany("INSERT OR IGNORE INTO books VALUES (?, ?, ?, ?, ?)", books_data)

    conn.commit()
    print("Mock data seeded successfully.")
    conn.close()

if __name__ == '__main__':
    initialize_database()
    seed_data()
    print("Setup complete. Run 'python app.py' to start the application.")