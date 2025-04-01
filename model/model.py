# Importing libraries
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import shap
import numpy as np
from rich.console import Console
import joblib

# Removing the already existing model to overwrite it with the new one
try:
    os.remove("deepshot.pkl")
except:
    pass

# Initialize rich console for pretty printing
console: Console = Console()

# Get the absolute path to the script's directory
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(BASE_DIR, "..", "data", "csv")  # Adjust for relative path
DATASET_FILE: str = os.path.join(DATA_DIR, "dataset.csv")

# Start spinner for data loading
with console.status("[green]Loading Data...") as status:
    # Load CSV Data
    df: pd.DataFrame = pd.read_csv(DATASET_FILE)
    status.update("Data Loaded Successfully!")

# Drop columns that are not used for training (just home_team and away_team)
df: pd.DataFrame = df.drop(["date", "home_team", "away_team"], axis=1)

# Drop irrelvant stats columns
stats_to_drop: list[str] = []
for stat in stats_to_drop:
    df: pd.DataFrame = df.drop([f"home_{stat}", f"away_{stat}"], axis=1)

# Define features (X) and target (y)
X: pd.DataFrame = df.drop(
    "winning_team", axis=1
)  # Features (all columns except 'winning_team')
y: pd.Series = df["winning_team"]  # Target variable (already 0 or 1)

# Split the data into training and test sets
console.print(
    "Splitting the dataset into training and testing sets...", style="bold cyan"
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train the Random Forest model with a progress bar
with console.status("[yellow]Training model... please wait.[/yellow]") as status:

    # Train the Random Forest model
    rf: RandomForestClassifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=18,
        min_samples_split=20,
        min_samples_leaf=20,
        max_features="sqrt",
        bootstrap=False,
        random_state=42,
    )
    rf.fit(X_train, y_train)

    status.update("[green]Model training complete![/green]")  # Update status once done

# Evaluate the model
console.print("Evaluating the model...", style="bold cyan")
y_pred: np.ndarray = rf.predict(X_test)
accuracy: float = accuracy_score(y_test, y_pred)

# Print the accuracy with rich styling
console.print(
    f"\n[bold green]Model Accuracy: {accuracy * 100:.2f}%[/bold green]", style="bold"
)

# Print detailed classification results with rich
console.print("\n[bold magenta]Classification Report:[/bold magenta]", style="bold")
console.print(classification_report(y_test, y_pred))

# Set options to display all columns
pd.set_option("display.max_columns", None)  # No column truncation
pd.set_option("display.width", None)  # Automatically adjust width
pd.set_option("display.max_rows", None)  # Show all rows, if necessary

# Now print the feature importance DataFrame
console.print("\n[bold yellow]Feature Importances:[/bold yellow]", style="bold")
feature_importances = rf.feature_importances_
features = X.columns  # Get the feature names

# Create a DataFrame to visualize feature importance
importance_df = pd.DataFrame({"Feature": features, "Importance": feature_importances})

# Sort by importance in descending order
importance_df = importance_df.sort_values(by="Importance", ascending=False)

console.print(importance_df)

# Reset Pandas display options to default (optional)
pd.reset_option("display.max_columns")
pd.reset_option("display.width")
pd.reset_option("display.max_rows")

# Save the model
joblib.dump(rf, "deepshot.pkl")

# Analyzing feature importance with SHAP values and chart
sample = X_test.sample(250, random_state=42)
explainer = shap.TreeExplainer(rf, sample)
shap_values = explainer(sample)
shap_values = shap_values[:, :, 1]
shap.summary_plot(shap_values, sample)
