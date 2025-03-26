# Importing libraries
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from skopt import BayesSearchCV
from skopt.space import Integer, Categorical
from rich.console import Console
import numpy as np

# Initialize rich console
console: Console = Console()

# Define paths
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(BASE_DIR, "..", "data", "csv")
DATASET_FILE: str = os.path.join(DATA_DIR, "dataset.csv")

# Load dataset
with console.status("[green]Loading Data...") as status:
    df: pd.DataFrame = pd.read_csv(DATASET_FILE)
    status.update("Data Loaded Successfully!")

# Drop non-training columns
df: pd.DataFrame = df.drop(["home_team", "away_team"], axis=1)
X: pd.DataFrame = df.drop("winning_team", axis=1)
y: pd.DataFrame = df["winning_team"]

# Split dataset
console.print(
    "Splitting the dataset into training and testing sets...", style="bold cyan"
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Define hyperparameter search space
param_space: dict[str, Integer | Categorical] = {
    "n_estimators": Integer(50, 300),
    "max_depth": Integer(3, 20),
    "min_samples_split": Integer(2, 20),
    "min_samples_leaf": Integer(1, 20),
    "max_features": Categorical(["sqrt", "log2"]),
    "bootstrap": Categorical([True, False]),
}

# Bayesian optimization
console.print("Starting Bayesian Hyperparameter Tuning...", style="bold yellow")
bayes_search: BayesSearchCV = BayesSearchCV(
    RandomForestClassifier(random_state=42),
    param_space,
    n_iter=30,  # Number of evaluations
    cv=5,  # 5-fold cross-validation
    n_jobs=-1,
    random_state=42,
)

# Train the model with hyperparameter tuning
with console.status(
    "[yellow]Optimizing hyperparameters... please wait.[/yellow]"
) as status:
    bayes_search.fit(X_train, y_train)
    status.update("[green]Hyperparameter tuning complete![/green]")

# Get the best model and parameters
best_params: dict[str, int | str] = bayes_search.best_params_
best_model: RandomForestClassifier = bayes_search.best_estimator_
console.print("Best Hyperparameters:", best_params, style="bold green")

# Evaluate the best model
y_pred: np.ndarray = best_model.predict(X_test)
accuracy: float = accuracy_score(y_test, y_pred)
console.print(
    f"\n[bold green]Best Model Accuracy: {accuracy * 100:.2f}%[/bold green]",
    style="bold",
)
console.print(
    "\n[bold magenta]Classification Report:[/bold magenta]",
    classification_report(y_test, y_pred),
)
