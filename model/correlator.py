# Importing libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# Loading the dataset
def load_data(file_path: str) -> pd.DataFrame:
    df: pd.DataFrame = pd.read_csv(file_path)
    return df.drop(["home_team", "away_team"], axis=1)


# Plot the selected features organized in a correlations matrix
def plot_correlation_matrix(df: pd.DataFrame, selected_features: list[str]) -> None:
    corr_matrix: pd.DataFrame = df[selected_features + ["winning_team"]].corr()
    plt.figure(figsize=(10, 6))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Feature Correlation Matrix")
    plt.show()


# Check the rolleation between a selected feature and all the features from the dataset
def check_feature_correlation(df: pd.DataFrame, feature: str):
    pd.set_option("display.max_columns", None)  # No column truncation
    pd.set_option("display.width", None)  # Automatically adjust width
    pd.set_option("display.max_rows", None)  # Show all rows, if necessary
    correlations: pd.DataFrame = df.corr()[feature].sort_values(ascending=False)
    print(f"\nCorrelation of {feature} with other features:\n")
    print(correlations)


# Incorporate all the correlator functionality in one simple main steps function
def main():
    file_path: str = "../data/csv/dataset.csv"  # Change if needed
    df: pd.DataFrame = load_data(file_path)
    print("Available Features:")
    print(df.columns.tolist())
    selected_features: list[str] = input(
        "Enter features to check correlation (comma-separated): "
    ).split(",")
    selected_features: list[str] = [
        feat.strip() for feat in selected_features if feat.strip() in df.columns
    ]
    if selected_features:
        plot_correlation_matrix(df, selected_features)
    check_feature: str = input("Enter a feature to check correlation with all others: ")
    if check_feature in df.columns:
        check_feature_correlation(df, check_feature)
    else:
        print("Feature not found in dataset.")


# Main section
if __name__ == "__main__":
    main()
