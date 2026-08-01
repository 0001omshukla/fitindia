"""
FitIndia Backend API
------------------------
Beginner-friendly explanation:

Until now, we've been running separate scripts one at a time in the
terminal. A "backend API" is different -- it's a program that STAYS
RUNNING and listens for requests, like a waiter taking orders.

For example: instead of running "python3 diet_engine.py" by hand,
a website can send a request like "give me a diet plan for member
FIT-8E6LE3" and this API will compute it and send back the answer
instantly -- this is exactly how real apps work behind the scenes.

We use FastAPI, a well-known, beginner-friendly Python framework
for building these APIs. Each "@app.get" or "@app.post" below
defines one "endpoint" -- a specific request the app can respond to.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import pickle
import sqlite3
from datetime import datetime

# Import logic from our existing modules (reusing everything we already built)
from diet_engine import load_food_database, recommend_diet
from progress_forecasting import analyze_progress
from checkin_system import get_connection, setup_tables, register_member, check_in, view_all_checkins
from payment_system import setup_payment_table, process_renewal, view_all_payments
from whatsapp_alerts import setup_alerts_table, trigger_alert, view_all_alerts
from login_system import setup_users_table, verify_login


app = FastAPI(title="FitIndia API")

# This allows a web dashboard (running in a browser) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the trained churn model once when the server starts (not every request --
# that would be slow. We keep it loaded in memory, ready to use instantly.)
with open("models/churn_model.pkl", "rb") as f:
    churn_model = pickle.load(f)


# ---------- Request "shapes" (what data the API expects to receive) ----------

class DietRequest(BaseModel):
    protein_target_g: float
    budget_rupees: float
    diet_pref: str  # "veg" or "nonveg"
    region_pref: str = None


class RegisterRequest(BaseModel):
    name: str


class CheckinRequest(BaseModel):
    member_code: str


class RenewalRequest(BaseModel):
    member_code: str
    plan: str  # "1_month", "3_month", "12_month"


class AlertRequest(BaseModel):
    member_code: str
    member_name: str
    alert_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Endpoints ----------

@app.get("/")
def home():
    """Serves the dashboard webpage directly, so the live URL shows the app itself."""
    return FileResponse("dashboard.html")


@app.get("/api-status")
def api_status():
    """A simple check to confirm the API is alive (moved from '/')."""
    return {"message": "FitIndia API is running!"}


@app.post("/auth/login")
def login(request: LoginRequest):
    """Checks username/password and returns whether login succeeded."""
    conn = get_connection()
    setup_users_table(conn)
    success = verify_login(conn, request.username, request.password)
    conn.close()
    return {"success": success}


@app.post("/diet/recommend")
def get_diet_recommendation(request: DietRequest):
    """Returns a diet plan based on protein target, budget, and preferences."""
    foods = load_food_database()
    result = recommend_diet(
        df=foods,
        goal="muscle_gain",
        protein_target_g=request.protein_target_g,
        budget_rupees=request.budget_rupees,
        diet_pref=request.diet_pref,
        region_pref=request.region_pref
    )
    return result


@app.get("/progress/analyze")
def get_progress_analysis():
    """Returns the progress trend analysis using the example log for now."""
    df = pd.read_csv("data/example_progress_log.csv")
    result = analyze_progress(df, goal="fat_loss")
    return result


@app.post("/members/register")
def api_register_member(request: RegisterRequest):
    """Registers a new member and gives them a unique check-in code."""
    conn = get_connection()
    setup_tables(conn)
    code = register_member(conn, request.name)
    conn.close()
    return {"name": request.name, "member_code": code}


@app.post("/members/checkin")
def api_check_in(request: CheckinRequest):
    """Logs a member check-in."""
    conn = get_connection()
    setup_tables(conn)
    success = check_in(conn, request.member_code)
    conn.close()
    return {"success": success}


@app.get("/members/checkins")
def api_view_checkins():
    """Returns every check-in ever logged."""
    conn = get_connection()
    setup_tables(conn)
    rows = view_all_checkins(conn)
    conn.close()
    return {"checkins": rows}


@app.post("/payments/renew")
def api_process_renewal(request: RenewalRequest):
    """Processes a simulated membership renewal payment."""
    conn = get_connection()
    setup_payment_table(conn)
    status = process_renewal(conn, request.member_code, request.plan)
    conn.close()
    return {"status": status}


@app.get("/payments/history")
def api_view_payments():
    conn = get_connection()
    setup_payment_table(conn)
    rows = view_all_payments(conn)
    conn.close()
    return {"payments": rows}


@app.post("/alerts/send")
def api_trigger_alert(request: AlertRequest):
    """Triggers a simulated WhatsApp alert for a member."""
    conn = get_connection()
    setup_alerts_table(conn)
    trigger_alert(conn, request.member_code, request.member_name, request.alert_type)
    conn.close()
    return {"sent": True}


@app.get("/alerts/history")
def api_view_alerts():
    conn = get_connection()
    setup_alerts_table(conn)
    rows = view_all_alerts(conn)
    conn.close()
    return {"alerts": rows}


@app.get("/churn/predict/{member_code}")
def predict_churn_for_member(member_code: str):
    """
    Predicts churn risk for a real member, using their check-in history
    (calculated from our checkins table) fed into our real trained model.
    """
    conn = get_connection()
    setup_tables(conn)

    cursor = conn.execute(
        "SELECT COUNT(*) FROM checkins WHERE member_code = ?", (member_code,)
    )
    checkin_count = cursor.fetchone()[0]
    conn.close()

    # NOTE: our trained model expects the same 13 columns as the Kaggle
    # dataset. For a brand-new real member we don't have all of that yet
    # (e.g. Age, Contract_period), so for now we build a placeholder row
    # using reasonable defaults plus their real check-in count. This is a
    # known simplification -- worth explaining honestly in an interview:
    # "the model works correctly when given full member profile data;
    # for brand-new members, some fields default to average values until
    # more real history is collected."
    sample_input = pd.DataFrame([{
        "gender": 1, "Near_Location": 1, "Partner": 0, "Promo_friends": 0,
        "Phone": 1, "Contract_period": 6, "Group_visits": 1, "Age": 28,
        "Avg_additional_charges_total": 50.0, "Month_to_end_contract": 3.0,
        "Lifetime": 1, "Avg_class_frequency_total": float(checkin_count),
        "Avg_class_frequency_current_month": float(checkin_count)
    }])

    prediction = churn_model.predict(sample_input)[0]
    probability = churn_model.predict_proba(sample_input)[0][1]

    return {
        "member_code": member_code,
        "churn_prediction": int(prediction),
        "churn_risk_probability": round(float(probability), 3)
    }
