# Importing libraries
import csv
import os
from rich.console import Console
from rich.progress import Progress

# Initialize the console for rich output
console: Console = Console()


# Merge the gamelogs and csv files to create the dataset
def create_dataset(
    schedule_file: str = "./csv/schedule.csv",
    gamelogs_file: str = "./csv/rolling_averages.csv",
    final_dataset_file: str = "./csv/dataset.csv",
):
    # Read schedule.csv into a list of dicts
    schedule: list = list()
    with open(schedule_file, mode="r") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            schedule.append(row)

    # Read gamelogs.csv into a list of dicts
    gamelogs: list = list()
    with open(gamelogs_file, mode="r") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            gamelogs.append(row)

    # Ensure the final dataset file is created and doesn't overwrite
    file_exists: bool = os.path.isfile(final_dataset_file)
    with open(final_dataset_file, mode="a", newline="") as file:
        writer: csv.writer = csv.writer(file)

        if not file_exists:
            # Write headers for the final dataset
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
                "home_ts",
                "home_ast_pct",
                "home_stl_pct",
                "home_blk_pct",
                "home_efg_pct",
                "home_tov_pct",
                "home_orb_pct",
                "home_ft_rate",
                "away_pts",
                "away_fg",
                "away_fga",
                "away_fg_pct",
                "away_fg3",
                "away_fg3a",
                "away_fg3_pct",
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
                "away_ts",
                "away_ast_pct",
                "away_stl_pct",
                "away_blk_pct",
                "away_efg_pct",
                "away_tov_pct",
                "away_orb_pct",
                "away_ft_rate",
            ]
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
                winner: str = game["winning_team"]

                # Initialize variables to store the stats
                home_stats = None
                away_stats = None

                # Check if stats exist for both teams on this date
                for gamelog in gamelogs:
                    if gamelog["date"] == date:
                        # Check if this is the home team's stats
                        if gamelog["team"] == home_team:
                            home_stats: dict[str, int | float] = {
                                f"home_{key}": gamelog[key]
                                for key in gamelog
                                if key != "date" and key != "team"
                            }
                        # Check if this is the away team's stats
                        elif gamelog["team"] == away_team:
                            away_stats: dict[str, int | float] = {
                                f"away_{key}": gamelog[key]
                                for key in gamelog
                                if key != "date" and key != "team"
                            }

                    # If we've found both home and away team stats, stop searching
                    if home_stats and away_stats:
                        break

                # If both home and away stats are found, create a row
                if home_stats and away_stats:
                    row: list[str] = (
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
    create_dataset()
    console.print(
        "[bold magenta]Dataset creation process completed!", style="bold green"
    )
