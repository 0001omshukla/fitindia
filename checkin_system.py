"""
FitIndia QR Check-in System
------------------------------
Beginner-friendly explanation:

Real gyms use fingerprint/RFID scanners to log when a member enters.
We don't have that hardware, so we simulate it with a QR code instead:

1. Each member gets a unique "member code" (like a secret ID).
2. In a real app, this code would be turned into a QR image the
   member shows at the door.
3. When "scanned" (here: typed in), we log that check-in with a
   timestamp into a real database (SQLite -- a lightweight database
   that lives in a single file, perfect for small projects like this).

This check-in data is exactly what feeds our churn model later:
"Avg_class_frequency" in the Kaggle dataset = basically how often
someone checks in. Once your app has real check-in history, you can
calculate this same feature for real members.
"""

import sqlite3
import random
import string
from datetime import datetime


def get_connection(db_path="data/fitindia.db"):
    """Connect to (or create) our database file."""
    conn = sqlite3.connect(db_path)
    return conn


def setup_tables(conn):
    """
    Create two tables if they don't already exist:
    - members: stores each member's info + their unique code
    - checkins: stores every check-in event (member + timestamp)
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            member_code TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_code TEXT NOT NULL,
            checkin_time TEXT NOT NULL
        )
    """)
    conn.commit()


def generate_member_code():
    """Generate a random unique code, e.g. 'FIT-8X3K9Q'."""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"FIT-{random_part}"


def register_member(conn, name):
    """Add a new member and give them a unique code."""
    code = generate_member_code()
    conn.execute(
        "INSERT INTO members (name, member_code) VALUES (?, ?)",
        (name, code)
    )
    conn.commit()
    print(f"Registered '{name}' with member code: {code}")
    return code


def check_in(conn, member_code):
    """
    Simulate a member scanning their QR code at the gym door.
    Logs the check-in with the current date/time.
    """
    # First, confirm this member code actually exists
    cursor = conn.execute(
        "SELECT name FROM members WHERE member_code = ?", (member_code,)
    )
    row = cursor.fetchone()

    if row is None:
        print(f"Check-in FAILED: no member found with code {member_code}")
        return False

    name = row[0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO checkins (member_code, checkin_time) VALUES (?, ?)",
        (member_code, now)
    )
    conn.commit()
    print(f"Check-in SUCCESS: {name} ({member_code}) checked in at {now}")
    return True


def view_all_checkins(conn):
    """See every check-in logged so far, newest first."""
    cursor = conn.execute("""
        SELECT c.checkin_time, m.name, c.member_code
        FROM checkins c
        JOIN members m ON c.member_code = m.member_code
        ORDER BY c.checkin_time DESC
    """)
    return cursor.fetchall()


# ---- DEMO: try the whole flow ----
if __name__ == "__main__":
    conn = get_connection()
    setup_tables(conn)

    print("Step 1: Registering a new member...")
    code = register_member(conn, "Om Shukla")

    print("\nStep 2: Simulating that member checking in today...")
    check_in(conn, code)

    print("\nStep 3: Simulating a WRONG code (should fail safely)...")
    check_in(conn, "FIT-FAKE99")

    print("\nStep 4: Viewing all check-ins logged so far...")
    for row in view_all_checkins(conn):
        print(" -", row)

    conn.close()
