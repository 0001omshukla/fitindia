"""
FitIndia Login System
-------------------------
Beginner-friendly explanation:

We store a "gym owner" username + password in our database.
We NEVER store the actual password as plain text (bad practice --
if someone got access to the database file, they'd see every
password directly). Instead we store a "hash" -- a scrambled,
one-way version of the password. When someone tries to log in, we
hash what they typed and compare it to the stored hash. If they
match, the password was correct -- but we never had to store or
even look at the real password itself.

This uses Python's built-in hashlib (no extra install needed).
"""

import sqlite3
import hashlib


def get_connection(db_path="data/fitindia.db"):
    return sqlite3.connect(db_path)


def setup_users_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()


def hash_password(password):
    """Turns a real password into a scrambled hash."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(conn, username, password):
    """Register a new gym-owner login (run once to set yours up)."""
    password_hash = hash_password(password)
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    conn.commit()
    print(f"User '{username}' created successfully.")


def verify_login(conn, username, password):
    """Check if the given username+password is correct."""
    cursor = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()
    if row is None:
        return False  # no such username

    stored_hash = row[0]
    return hash_password(password) == stored_hash


# ---- SETUP: run this once to create your own gym-owner login ----
if __name__ == "__main__":
    conn = get_connection()
    setup_users_table(conn)

    # CHANGE these to your own username/password before running!
    create_user(conn, "omshukla", "gym123")

    print("\nTesting login with correct password...")
    print("Login success?", verify_login(conn, "omshukla", "gym123"))

    print("\nTesting login with WRONG password...")
    print("Login success?", verify_login(conn, "omshukla", "wrongpass"))

    conn.close()
