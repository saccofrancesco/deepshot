# Importing libraries
import csv
import os
from rich.console import Console
from rich.progress import Progress
from collections import defaultdict

# Initialize the console for rich output
console: Console = Console()

# Get the absolute path of the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))


# Merge the gamelogs and csv files to create the dataset
def create_dataset(
    schedule_file: str,
    gamelogs_file: str,
    final_dataset_file: str,
):
    # Convert relative paths to absolute paths based on the script's directory
    schedule_file: str = os.path.join(script_dir, schedule_file)
    gamelogs_file: str = os.path.join(script_dir, gamelogs_file)
    final_dataset_file: str = os.path.join(script_dir, final_dataset_file)

    # Read schedule.csv into a list of dicts
    schedule: list = []
    with open(schedule_file, mode="r") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            schedule.append(row)

    # Read gamelogs.csv into a list of dicts and create a dictionary for fast lookups
    gamelogs_dict = defaultdict(dict)
    with open(gamelogs_file, mode="r") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            date: str = row["date"]
            team: str = row["team"]
            gamelogs_dict[(date, team)] = {
                f"{team}_{key}": value
                for key, value in row.items()
                if key not in ["date", "team"]
            }

    # Check if the file already exists and remove it
    if os.path.exists(final_dataset_file):
        os.remove(final_dataset_file)

    # Creating the file and the headers
    headers: list[str] = [
        "home_team",
        "away_team",
        "winning_team",
        "home_pts",
        "home_fg",
        "home_fga",
        "home_fg_pct",
        "home_fg3",
        "home_fg3a",
        "home_fg3_pct",
        "home_fg2",
        "home_fg2a",
        "home_fg2_pct",
        "home_ft",
        "home_fta",
        "home_ft_pct",
        "home_orb",
        "home_drb",
        "home_trb",
        "home_ast",
        "home_stl",
        "home_blk",
        "home_tov",
        "home_pf",
        "home_ortg",
        "home_drtg",
        "home_pace",
        "home_ftr",
        "home_3ptar",
        "home_ts",
        "home_trb_pct",
        "home_ast_pct",
        "home_stl_pct",
        "home_blk_pct",
        "home_efg_pct",
        "home_tov_pct",
        "home_orb_pct",
        "home_ft_rate",
        "home_poss",
        "home_usg_pct",
        "away_pts",
        "away_fg",
        "away_fga",
        "away_fg_pct",
        "away_fg3",
        "away_fg3a",
        "away_fg3_pct",
        "away_fg2",
        "away_fg2a",
        "away_fg2_pct",
        "away_ft",
        "away_fta",
        "away_ft_pct",
        "away_orb",
        "away_drb",
        "away_trb",
        "away_ast",
        "away_stl",
        "away_blk",
        "away_tov",
        "away_pf",
        "away_ortg",
        "away_drtg",
        "away_pace",
        "away_ftr",
        "away_3ptar",
        "away_ts",
        "away_trb_pct",
        "away_ast_pct",
        "away_stl_pct",
        "away_blk_pct",
        "away_efg_pct",
        "away_tov_pct",
        "away_orb_pct",
        "away_ft_rate",
        "away_poss",
        "away_usg_pct",
    ]

    with open(final_dataset_file, mode="a", newline="") as file:
        writer: csv.writer = csv.writer(file)
        writer.writerow(headers)

        # Initialize a progress bar for the game processing
        with Progress() as progress:
            task: int = progress.add_task(
                "[cyan]Processing games...", total=len(schedule)
            )

            # Process each game in the schedule and find the relevant game logs
            for game in schedule:
                date: str = game["date"]
                home_team: str = game["home_team"]
                away_team: str = game["away_team"]
                winner: int = game["winning_team"]

                # Lookup stats for both teams from the gamelogs_dict
                home_stats: dict = gamelogs_dict.get((date, home_team), {})
                away_stats: dict = gamelogs_dict.get((date, away_team), {})

                # If both home and away stats are found, create a row
                if home_stats and away_stats:
                    row: str = (
                        [home_team, away_team, winner]
                        + list(home_stats.values())
                        + list(away_stats.values())
                    )
                    writer.writerow(row)

                # Update the progress bar
                progress.update(task, advance=1)

    # Display a success message
    console.print(
        f"Final dataset successfully saved to {final_dataset_file} ✅",
        style="bold green",
    )


# Main
if __name__ == "__main__":
    console.print(
        "[bold magenta]Starting the dataset creation process...", style="bold blue"
    )
    create_dataset("csv/training_schedule.csv", "csv/averages.csv", "csv/dataset.csv")
    console.print(
        "[bold magenta]Dataset creation process completed!", style="bold green"
    )
