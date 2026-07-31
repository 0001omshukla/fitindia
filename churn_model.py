"""
FitIndia Churn Prediction Model
----------------------------------
Beginner-friendly explanation:

We have 4000 real gym members' data. Each row has info about a member
(age, attendance, contract length, etc.) and whether they churned
(left the gym) or not.

Our goal: teach a model to look at a NEW member's info and predict
"will this person likely churn or not?"

Step 1: Split data into TRAIN (80%) and TEST (20%).
  - TRAIN: the model learns patterns from this.
  - TEST: we hide this from the model during training, then use it
    to check if the model actually learned something real (not just
    memorized the training data).

Step 2: Train a Random Forest model.
  - A Random Forest is like asking 100 different "decision trees"
    (simple yes/no question flowcharts) to each vote on whether a
    member will churn, then taking the majority vote. This makes it
    more accurate and less likely to overfit than a single tree.

Step 3: Check accuracy on the TEST data (data it has never seen).

Step 4: Find out which columns mattered most (feature importance) --
  this tells us WHY the model makes its predictions, which is
  important for explaining it in an interview.

Step 5: Save the trained model to a file so we can reuse it later.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle


def load_data(csv_path="data/gym_churn_us.csv"):
    """Step 0: Load the real dataset."""
    df = pd.read_csv(csv_path)
    return df


def train_churn_model(df):
    """Steps 1-3: Split data, train the model, test its accuracy."""

    # X = all the columns we use to PREDICT (everything except Churn)
    # y = the answer we're trying to predict (the Churn column itself)
    X = df.drop("Churn", axis=1)
    y = df["Churn"]

    # Step 1: split into 80% train, 20% test
    # random_state=42 just makes the split repeatable every time we run this
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Step 2: train a Random Forest with 100 trees
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Step 3: test on data the model has NEVER seen
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    return model, X_test, y_test, predictions, accuracy, X.columns


def show_feature_importance(model, feature_names):
    """Step 4: Which columns mattered most in predicting churn?"""
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)
    return importance_df


def save_model(model, path="models/churn_model.pkl"):
    """Step 5: Save the trained model to a file for reuse later."""
    with open(path, "wb") as f:
        pickle.dump(model, f)


# ---- RUN EVERYTHING ----
if __name__ == "__main__":
    print("Loading real gym churn data (4000 members)...\n")
    df = load_data()

    print("Training the model (this takes a few seconds)...\n")
    model, X_test, y_test, predictions, accuracy, feature_names = train_churn_model(df)

    print(f"=== MODEL ACCURACY ON UNSEEN DATA: {accuracy * 100:.1f}% ===\n")

    print("=== Detailed performance report ===")
    print(classification_report(y_test, predictions, target_names=["Stayed", "Churned"]))

    print("=== What mattered most in predicting churn? ===")
    importance_df = show_feature_importance(model, feature_names)
    print(importance_df.to_string(index=False))

    print("\nSaving trained model to models/churn_model.pkl ...")
    save_model(model)
    print("Done! Model saved.")
