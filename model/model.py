# Importing libraries
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
from rich.console import Console
import joblib

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
df: pd.DataFrame = df.drop(["home_team", "away_team"], axis=1)

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
        n_estimators=200,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=4,
        max_features="log2",
        bootstrap=False,
        class_weight=None,
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

# Save the model
joblib.dump(rf, "deepshot.pkl")
