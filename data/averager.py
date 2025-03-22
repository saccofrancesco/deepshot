import pandas as pd
import os
from rich.console import Console

# Initialize rich console
console: Console = Console()

# Get the absolute path to the script's directory
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
CSV_DIR: str = os.path.join(BASE_DIR, "csv")

# Define file paths
GAMELOGS_FILE: str = os.path.join(CSV_DIR, "gamelogs.csv")
OUTPUT_FILE: str = os.path.join(CSV_DIR, "rolling_averages.csv")

# Game window size
GAME_WINDOW: int = 25


def compute_rolling_averages(
    game_window: int, gamelogs_file: str = GAMELOGS_FILE, output_file: str = OUTPUT_FILE
):
    # Load the CSV file
    console.print("[bold green]Loading CSV file...[/bold green]")
    df: pd.DataFrame = pd.read_csv(gamelogs_file)

    # Sort by team and date
    console.print("[bold green]Sorting data by team and date...[/bold green]")
    df["date"] = pd.to_datetime(df["date"])
    df: pd.DataFrame = df.sort_values(by=["team", "date"])

    # Identify columns for rolling averages (excluding 'date' and 'team')
    stat_columns: list[str] = [col for col in df.columns if col not in ["date", "team"]]

    # Compute rolling averages
    console.print("[bold green]Computing rolling averages...[/bold green]")

    def compute_rolling_avg(group: pd.DataFrame) -> pd.DataFrame:
        rolling_avg: pd.DataFrame = (
            group[stat_columns]
            .rolling(window=game_window, min_periods=1)
            .mean()
            .shift(1)
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
    compute_rolling_averages(25)
