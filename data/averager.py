# Importing libraries
import pandas as pd
import os
from rich.console import Console

# Initialize rich console
console: Console = Console()

# Get the absolute path to the script's directory
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
CSV_DIR: str = os.path.join(BASE_DIR, "csv")
TEST_DIR: str = os.path.join(BASE_DIR, "test")

# Define file paths
GAMELOGS_FILE: str = os.path.join(CSV_DIR, "gamelogs.csv")
OUTPUT_FILE: str = os.path.join(CSV_DIR, "averages.csv")

# Game window size
game_window: int = 25


# Calculate the rolling average over the last n game_window games
def compute_rolling_averages(game_window: int, gamelogs_file: str, output_file: str):
    # Load the CSV file
    console.print("[bold green]Loading CSV file...[/bold green]")
    df: pd.DataFrame = pd.read_csv(gamelogs_file)

    # Sort by team and date
    console.print("[bold green]Sorting data by team and date...[/bold green]")
    df["date"] = pd.to_datetime(df["date"])
    df: pd.DataFrame = df.sort_values(by=["team", "date"])

    # Identify columns for rolling averages (excluding 'date' and 'team')
    stat_columns: list[str] = [col for col in df.columns if col not in ["date", "team"]]

    # Feature engeneering
    df["ast_to_tov_"] = round(df["ast"] / df["tov"], 2)

    # Compute rolling averages
    console.print("[bold green]Computing rolling averages...[/bold green]")

    def compute_rolling_avg(group: pd.DataFrame) -> pd.DataFrame:
        rolling_avg: pd.DataFrame = (
            group[stat_columns].ewm(span=game_window, adjust=False).mean().shift(1)
        )
        rolling_avg.iloc[0] = group.iloc[0][stat_columns]
        return rolling_avg

    df[stat_columns] = df.groupby("team", group_keys=False, observed=True)[
        stat_columns
    ].apply(compute_rolling_avg)

    # Limit decimal places to 2
    console.print("[bold green]Rounding values...[/bold green]")
    df[stat_columns] = df[stat_columns].round(2)

    # Save to CSV
    if os.path.exists(output_file):
        console.print(
            f"[bold yellow]File {output_file} already exists. Removing...[/bold yellow]"
        )
        os.remove(output_file)

    df.to_csv(output_file, index=False)
    console.print(f"[bold cyan]Rolling averages saved to {output_file}[/bold cyan]")


# Run only when executed directly
if __name__ == "__main__":
    compute_rolling_averages(game_window, GAMELOGS_FILE, OUTPUT_FILE)
