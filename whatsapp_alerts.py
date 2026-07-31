"""
FitIndia Simulated WhatsApp Alert System
--------------------------------------------
Beginner-friendly explanation:

Real WhatsApp alerts (via Twilio) work like this:
1. Your code decides WHO to message and WHAT to say
   (e.g. "high churn risk member" -> "We miss you! Here's 20% off")
2. Your code calls Twilio's API with that phone number + message
3. Twilio delivers it to the person's real WhatsApp

Since going through Twilio's real signup is taking too long right
now, we simulate step 2 -- instead of actually sending it, we PRINT
the message and LOG it into our database, exactly as if it had been
sent. The decision-making logic (who gets what message, and why) is
identical either way -- that's the actual "smart" part of this
module, not the sending mechanism itself.

This can be swapped for real Twilio later by replacing just the
send_whatsapp_message() function with a real API call -- everything
else stays the same.
"""

import sqlite3
from datetime import datetime


def get_connection(db_path="data/fitindia.db"):
    return sqlite3.connect(db_path)


def setup_alerts_table(conn):
    """Create a table to store every alert we've ever sent."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_code TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_time TEXT NOT NULL
        )
    """)
    conn.commit()


def build_message(alert_type, member_name):
    """
    Decide WHAT message to send, based on the type of alert.
    This is the "smart" decision-making part of the module.
    """
    messages = {
        "high_churn_risk": (
            f"Hi {member_name}, we miss you at the gym! 💪 "
            f"Here's a free personal training session this week -- come say hi!"
        ),
        "payment_failed": (
            f"Hi {member_name}, your last payment didn't go through. "
            f"Please retry to keep your membership active without interruption."
        ),
        "progress_plateau": (
            f"Hi {member_name}, your progress has slowed a bit recently. "
            f"Check the app for a quick tip to get back on track!"
        ),
        "welcome": (
            f"Welcome to FitIndia, {member_name}! We're excited to have you. "
            f"Log your first workout today to get started."
        ),
    }
    return messages.get(alert_type, f"Hi {member_name}, you have a new update from FitIndia.")


def send_whatsapp_message(member_code, member_name, alert_type):
    """
    STEP that would call the REAL Twilio API in a production version.
    Right now, it simulates the send by printing + logging it.
    """
    message = build_message(alert_type, member_name)

    # --- This is where the real Twilio API call would go instead ---
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # client.messages.create(from_='whatsapp:+14155238886',
    #                         to=f'whatsapp:{member_phone}',
    #                         body=message)
    # ------------------------------------------------------------------

    print(f"[SIMULATED WHATSAPP] To: {member_name} ({member_code})")
    print(f"    Message: {message}")

    return message


def log_alert(conn, member_code, alert_type, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO alerts (member_code, alert_type, message, sent_time)
        VALUES (?, ?, ?, ?)
    """, (member_code, alert_type, message, now))
    conn.commit()


def trigger_alert(conn, member_code, member_name, alert_type):
    """Runs the full flow: decide message -> send (simulated) -> log it."""
    message = send_whatsapp_message(member_code, member_name, alert_type)
    log_alert(conn, member_code, alert_type, message)
    print(f"Alert logged successfully.\n")


def view_all_alerts(conn):
    cursor = conn.execute("""
        SELECT sent_time, member_code, alert_type, message
        FROM alerts
        ORDER BY sent_time DESC
    """)
    return cursor.fetchall()


# ---- DEMO: simulate a few real alerts ----
if __name__ == "__main__":
    conn = get_connection()
    setup_alerts_table(conn)

    member_code = "FIT-8E6LE3"
    member_name = "Om Shukla"

    print("Simulating a HIGH CHURN RISK alert (from our churn model)...\n")
    trigger_alert(conn, member_code, member_name, "high_churn_risk")

    print("Simulating a PROGRESS PLATEAU alert (from our forecasting module)...\n")
    trigger_alert(conn, member_code, member_name, "progress_plateau")

    print("All alerts logged so far:")
    for row in view_all_alerts(conn):
        print(" -", row)

    conn.close()
