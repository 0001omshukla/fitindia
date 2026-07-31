"""
FitIndia Diet Engine
---------------------
Beginner-friendly explanation:
This script reads our food database (indian_foods.csv) and picks a
combination of foods that gets close to a person's protein target,
without going over their budget.

How the "picking" works (simple, no fancy ML needed here):
1. We calculate "protein per rupee" for every food (how much protein
   you get for every 1 rupee spent). This tells us which foods are
   the best VALUE for protein.
2. We sort foods by best value first (cheapest protein first).
3. We keep adding foods (greedy approach) until we hit the protein
   target or run out of budget -- whichever happens first.

This is called a "greedy algorithm" -- a simple, explainable way to
solve a "best combination under a limit" problem. It's not deep
learning, and that's fine -- it's the right tool for this problem.
"""

import pandas as pd

def load_food_database(csv_path="data/indian_foods.csv"):
    """Step 1: Read the food database file into a table we can work with."""
    df = pd.read_csv(csv_path)
    return df


def recommend_diet(df, goal, protein_target_g, budget_rupees, diet_pref, region_pref=None):
    """
    Step 2: Pick foods to hit the protein target within budget.

    Parameters (what YOU provide):
    - goal: "fat_loss" or "muscle_gain" (used later to adjust calories, not shown yet)
    - protein_target_g: how many grams of protein you want today (e.g. 100)
    - budget_rupees: how much you're willing to spend on food today (e.g. 200)
    - diet_pref: "veg" or "nonveg" (nonveg means both veg+nonveg allowed)
    - region_pref: optional, e.g. "South Indian" to prefer that region's foods
    """

    # Filter: keep only foods matching diet preference
    if diet_pref == "veg":
        available = df[df["veg_or_nonveg"] == "veg"].copy()
    else:
        available = df.copy()  # nonveg users can eat both veg and nonveg foods

    # Optional: if user gave a region preference, prioritize that region first
    if region_pref:
        available["region_match"] = available["region"].apply(
            lambda r: 0 if (r == region_pref or r == "Pan India") else 1
        )
        available = available.sort_values("region_match")

    # Step 2a: calculate "protein per rupee" for every food = value score
    available["protein_per_rupee"] = available["protein_g"] / available["cost_rupees"]

    # Step 2b: sort foods by best protein-value first (greedy approach)
    available = available.sort_values("protein_per_rupee", ascending=False)

    # Step 2c: greedily pick foods until protein target or budget is hit
    plan = []
    total_protein = 0
    total_cost = 0
    total_calories = 0

    for _, food in available.iterrows():
        if total_protein >= protein_target_g:
            break
        if total_cost + food["cost_rupees"] > budget_rupees:
            continue  # skip this food, it would break the budget

        plan.append(food["food_name"] + " (" + food["serving_size"] + ")")
        total_protein += food["protein_g"]
        total_cost += food["cost_rupees"]
        total_calories += food["calories"]

    return {
        "plan": plan,
        "total_protein_g": round(total_protein, 1),
        "total_cost_rupees": round(total_cost, 1),
        "total_calories": round(total_calories, 1),
        "protein_target_met": total_protein >= protein_target_g
    }


# ---- DEMO: try it out with an example person ----
if __name__ == "__main__":
    foods = load_food_database()

    print("Example: A vegetarian in South India wanting 80g protein, budget Rs.150/day\n")

    result = recommend_diet(
        df=foods,
        goal="muscle_gain",
        protein_target_g=80,
        budget_rupees=150,
        diet_pref="veg",
        region_pref="South Indian"
    )

    print("Recommended foods for today:")
    for item in result["plan"]:
        print(" -", item)

    print("\nTotal protein:", result["total_protein_g"], "g")
    print("Total cost: Rs.", result["total_cost_rupees"])
    print("Total calories:", result["total_calories"])
    print("Protein target met?", result["protein_target_met"])
