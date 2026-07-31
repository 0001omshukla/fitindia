"""
FitIndia Simulated Payment System
------------------------------------
Beginner-friendly explanation:

Real payment gateways like Razorpay work in 3 steps:
1. CREATE ORDER -- the business creates a "bill" (e.g. "Rs.1500 for
   1-month membership renewal") and gets an order_id back.
2. MEMBER PAYS -- the member completes payment on a checkout screen.
3. VERIFY & LOG -- once payment succeeds, the business verifies it
   and records the renewal in their system.

Since we can't reach Razorpay's real servers without full business
KYC, we simulate the exact same 3 steps locally. The CODE STRUCTURE
is intentionally the same as a real integration -- so this can be
swapped for the real Razorpay API later with minimal changes.

This also logs every successful renewal into our same fitindia.db
database, so it connects to the rest of the project (a member's
payment history feeds into the churn model's "additional charges"
and "renewal" signals).
"""

import sqlite3
import random
import string
from datetime import datetime


def get_connection(db_path="data/fitindia.db"):
    return sqlite3.connect(db_path)


def setup_payment_table(conn):
    """Create a table to store all payment/renewal records."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_code TEXT NOT NULL,
            order_id TEXT NOT NULL,
            amount_rupees REAL NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            payment_time TEXT NOT NULL
        )
    """)
    conn.commit()


def create_order(member_code, plan):
    """
    STEP 1: Create an order (like Razorpay's order.create() API).
    Returns an order_id and the amount based on the chosen plan.
    """
    plan_prices = {
        "1_month": 1500,
        "3_month": 4000,
        "12_month": 12000
    }

    if plan not in plan_prices:
        raise ValueError("Plan must be one of: 1_month, 3_month, 12_month")

    amount = plan_prices[plan]
    order_id = "order_" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    print(f"Order created: {order_id} | Plan: {plan} | Amount: Rs.{amount}")
    return order_id, amount


def simulate_payment(order_id, amount):
    """
    STEP 2: Simulate the member paying (in real Razorpay, this
    happens on their checkout page). We simulate a 95% success rate,
    since real payments can occasionally fail (card declined, etc.)
    -- this makes our simulation more realistic than assuming
    every payment always succeeds.
    """
    success = random.random() < 0.95  # 95% of payments succeed
    status = "SUCCESS" if success else "FAILED"
    print(f"Payment attempt for {order_id}: {status}")
    return status


def verify_and_log_payment(conn, member_code, order_id, amount, plan, status):
    """
    STEP 3: Log the final result into our database, whether it
    succeeded or failed -- just like a real system would keep a
    record either way.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO payments (member_code, order_id, amount_rupees, plan, status, payment_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (member_code, order_id, amount, plan, status, now))
    conn.commit()


def process_renewal(conn, member_code, plan):
    """
    Runs the full 3-step flow together, like a real checkout button
    would trigger behind the scenes.
    """
    order_id, amount = create_order(member_code, plan)
    status = simulate_payment(order_id, amount)
    verify_and_log_payment(conn, member_code, order_id, amount, plan, status)

    if status == "SUCCESS":
        print(f"✅ Renewal confirmed for {member_code} ({plan}, Rs.{amount})")
    else:
        print(f"❌ Renewal failed for {member_code} -- member should retry payment")

    return status


def view_all_payments(conn):
    cursor = conn.execute("""
        SELECT payment_time, member_code, plan, amount_rupees, status
        FROM payments
        ORDER BY payment_time DESC
    """)
    return cursor.fetchall()


# ---- DEMO: run the full simulated flow ----
if __name__ == "__main__":
    conn = get_connection()
    setup_payment_table(conn)

    # Using the same member code we registered earlier in checkin_system.py
    member_code = "FIT-8E6LE3"  # replace with your own real code if different

    print("Simulating a membership renewal...\n")
    process_renewal(conn, member_code, "3_month")

    print("\nAll payment records so far:")
    for row in view_all_payments(conn):
        print(" -", row)

    conn.close()
