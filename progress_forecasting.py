"""
FitIndia Progress Forecasting Module
--------------------------------------
Beginner-friendly explanation:

We have weekly weight readings, like: 80.0, 79.6, 79.3, 79.0, 78.8, 78.7

Step 1: We look at how much weight was lost EACH week (week-to-week change).
  Week1->2: -0.4kg   Week2->3: -0.3kg   Week3->4: -0.3kg
  Week4->5: -0.2kg   Week5->6: -0.1kg

Step 2: We compare the EARLY weeks' average change vs the RECENT weeks'
average change. If recent weeks are losing much less than early weeks,
that means progress is slowing down (a "plateau" forming).

Step 3: Based on that comparison, we give a simple, clear recommendation.

This uses basic math (averages and simple linear regression), not deep
learning -- and that's the right choice here because the pattern is
simple and needs to be explainable to a real person, not a black box.
"""

import pandas as pd
import numpy as np


def load_progress_log(csv_path="data/example_progress_log.csv"):
    """Step 1: Read the person's weekly logged data."""
    return pd.read_csv(csv_path)


def analyze_progress(df, goal="fat_loss"):
    """
    Step 2: Detect the trend and generate a recommendation.

    goal: "fat_loss" or "muscle_gain" -- changes how we interpret the trend.
    """

    weights = df["weight_kg"].values

    # Week-to-week change in weight (a list of differences)
    weekly_changes = np.diff(weights)  # e.g. [-0.4, -0.3, -0.3, -0.2, -0.1]

    # Split into "early" half and "recent" half to compare pace of change
    half = len(weekly_changes) // 2
    early_avg_change = weekly_changes[:half].mean()
    recent_avg_change = weekly_changes[half:].mean()

    # Fit a simple straight-line trend through ALL the weight data
    # (linear regression: slope tells us kg change per week, on average)
    weeks = df["week_number"].values
    slope, intercept = np.polyfit(weeks, weights, 1)

    result = {
        "early_avg_weekly_change_kg": round(early_avg_change, 2),
        "recent_avg_weekly_change_kg": round(recent_avg_change, 2),
        "overall_trend_slope_kg_per_week": round(slope, 3),
    }

    # Step 3: Turn the numbers into a plain-English recommendation
    if goal == "fat_loss":
        if recent_avg_change >= -0.05:
            result["status"] = "Plateaued"
            result["recommendation"] = (
                "Your weight loss has basically stopped in recent weeks. "
                "Try reducing daily intake by 150-200 kcal, or add 1 extra "
                "cardio session per week."
            )
        elif abs(recent_avg_change) < abs(early_avg_change) * 0.6:
            result["status"] = "Slowing down"
            result["recommendation"] = (
                f"Your weekly loss has slowed from about {round(abs(early_avg_change), 2)}kg "
                f"to about {round(abs(recent_avg_change), 2)}kg per week. Consider a small "
                "calorie reduction (100-150 kcal/day) if you want to keep the pace up."
            )
        else:
            result["status"] = "On track"
            result["recommendation"] = "Good pace of fat loss -- keep doing what you're doing."

    elif goal == "muscle_gain":
        # For muscle gain we'd normally look at workout_volume_kg trend too
        volume_slope, _ = np.polyfit(weeks, df["workout_volume_kg"].values, 1)
        result["workout_volume_trend_per_week"] = round(volume_slope, 1)
        if volume_slope <= 0:
            result["status"] = "Stalled"
            result["recommendation"] = (
                "Your lifting volume isn't increasing. Try adding more protein "
                "or increasing weight/reps gradually (progressive overload)."
            )
        else:
            result["status"] = "Progressing"
            result["recommendation"] = "Your training volume is increasing well -- keep it up."

    return result


# ---- DEMO: run it on the example data ----
if __name__ == "__main__":
    df = load_progress_log()
    print("Weekly logged data:")
    print(df.to_string(index=False))
    print()

    result = analyze_progress(df, goal="fat_loss")

    print("=== Progress Analysis (Fat Loss Goal) ===")
    for key, value in result.items():
        print(f"{key}: {value}")
