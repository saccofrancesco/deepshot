# Step 1: Import Libraries
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
import plotly.express as px
import joblib
import os

# Step 2: Load CSV Data
df = pd.read_csv("../data/csv/dataset.csv")

# Step 3: Drop columns that are not used for training (just home_team and away_team)
df = df.drop(["home_team", "away_team"], axis=1)

# Step 4: Define features (X) and target (y)
X = df.drop("winning_team", axis=1)  # Features (all columns except 'winning_team')
y = df["winning_team"]  # Target variable (already 0 or 1)

# Step 5: Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

if not os.path.exists("best_random_forest.pkl"):
    # Step 6: Define the parameter grid for RandomForest
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }

    # Initialize Random Forest classifier
    rf = RandomForestClassifier(random_state=42)

    # Setup GridSearchCV with cross-validation (cv=5)
    grid_search = GridSearchCV(
        estimator=rf, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2
    )

    # Fit the model to the training data
    grid_search.fit(X_train, y_train)

    # Step 7: Best parameters from grid search
    print(f"Best parameters: {grid_search.best_params_}")

    # Step 8: Get the best estimator (best Random Forest model)
    best_rf = grid_search.best_estimator_

    # Step 9: Evaluate the model on the test set
    y_pred = best_rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy after tuning: {accuracy * 100:.2f}%")

    # Save the best model (after GridSearchCV)
    joblib.dump(best_rf, "best_random_forest.pkl")
    print("✅ Best model saved successfully!")
else:
    # Load the saved model (No need for retraining)
    best_rf = joblib.load("best_random_forest.pkl")
    print("✅ Best model loaded successfully!")

    # Get feature importance
    feature_importance_df = pd.DataFrame(
        {"Feature": X_train.columns, "Importance": best_rf.feature_importances_}
    ).sort_values(by="Importance", ascending=False)

    # Plot with Plotly
    import plotly.express as px

    fig = px.bar(
        feature_importance_df,
        x="Importance",
        y="Feature",
        orientation="h",
        title="🔍 Important Features Tier List",
        labels={"Importance": "Feature Importance"},
        color="Importance",
        color_continuous_scale="Blues",
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    fig.show()
