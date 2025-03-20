# Importing libraries
import pandas as pd
import pandas
import csv
import pandas.core
from rich.console import Console
from rich.progress import Progress

# Initialize rich console for printing
console: Console = Console()

# Game window size
game_window: int = 15

# Load game logs
gamelogs_filename: str = "./csv/gamelogs.csv"
df: pd.DataFrame = pd.read_csv(gamelogs_filename)


# Function to compute the average for each statistics
def compute_linear_weighted_avg(stats: list[int | float]) -> float:
    n: int = len(stats)
    if n == 0:
        return None  # No previous games available

    weights: list[int] = list(range(1, n + 1))  # Linear weights: 1, 2, 3, ..., n
    weighted_avg: float = sum(
        stat * weight for stat, weight in zip(stats, weights)
    ) / sum(weights)
    return round(weighted_avg, 2)  # Round to 2 decimal places


# Compute rolling averages
rolling_averages: list = list()

# Group by team and process each team
grouped: pandas.core.groupby.generic.DataFrameGroupBy = df.groupby("team")

# Initialize the progress bar
with Progress() as progress:
    task: int = progress.add_task("[cyan]Processing teams...", total=len(grouped))

    for team, games in grouped:
        games: pd.DataFrame = games.sort_values("date")
        for i, row in games.iterrows():
            prev_games: pd.DataFrame = games.iloc[
                max(0, i - game_window) : i
            ]  # Last 15 games before this one
            rolling_avg: dict[str, str | int | float] = {
                "date": row["date"],
                "team": row["team"],
            }

            # For each stat column (excluding 'date' and 'team')
            for col in df.columns[2:]:  # Exclude date and team columns
                rolling_avg[col] = (
                    compute_linear_weighted_avg(prev_games[col].tolist())
                    if not prev_games.empty
                    else round(row[col], 2)
                )

            rolling_averages.append(rolling_avg)

        # Update the progress bar after each team's processing
        progress.update(task, advance=1)

# Save to CSV
rolling_filename: str = "./csv/rolling_averages.csv"
with open(rolling_filename, mode="w", newline="") as file:
    writer: csv.DictWriter = csv.DictWriter(
        file, fieldnames=["date", "team"] + df.columns[2:].tolist()
    )  # Ensure we include all columns
    writer.writeheader()
    writer.writerows(rolling_averages)

# Print success message with rich
console.print(f"[bold green]Rolling averages saved to {rolling_filename}[/bold green]")
