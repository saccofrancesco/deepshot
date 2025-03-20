# Importing libraries
import pandas as pd
import os
from rich.console import Console

# Initialize rich console
console: Console = Console()

# Load the CSV file
console.print("[bold green]Loading CSV file...[/bold green]")
df: pd.DataFrame = pd.read_csv("./csv/gamelogs.csv")

# Game window
game_window: int = 30

# Sort by team and date
console.print("[bold green]Sorting data by team and date...[/bold green]")
df["date"] = pd.to_datetime(df["date"])
df: pd.DataFrame = df.sort_values(by=["team", "date"])

# Identify columns for rolling averages (excluding 'date' and 'team')
stat_columns: list[str] = [col for col in df.columns if col not in ["date", "team"]]

# Compute rolling averages
console.print("[bold green]Computing rolling averages...[/bold green]")


# Function to calculate the rolling average for the specified game window on on stat group
def compute_rolling_avg(group: pd.DataFrame) -> pd.DataFrame:
    rolling_avg: pd.DataFrame = (
        group[stat_columns].rolling(window=game_window, min_periods=1).mean().shift(1)
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
path: str = "./csv/rolling_averages.csv"

if os.path.exists(path):
    console.print(f"[bold yellow]File {path} already exists. Removing...[/bold yellow]")
    os.remove(path)

df.to_csv(path, index=False)
console.print(f"[bold cyan]Rolling averages saved to {path}[/bold cyan]")
