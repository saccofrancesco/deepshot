# Importing libraries
import requests
import bs4
from collections import defaultdict
import pandas as pd
import os
from rich.console import Console
from rich.progress import Progress
import time
import csv
import datetime

# Initialize a Rich console
console: Console = Console()

# Storing the teams names - codes pair
team_codes: dict[str, str] = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHO",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}


# Get all the team season log basic and andvanced statistics
def fetch_team_season_log(
    team: str, season: str
) -> dict[str, dict[str, dict[str, int | float]]]:

    # Visualizing the current team and season infos
    console.print(
        f"[bold green]Fetching data for {team} - {season} season...[/bold green]"
    )

    # Constructing the URLs
    basic_url: str = (
        f"https://www.basketball-reference.com/teams/{team_codes[team]}/{season}/gamelog/"
    )
    advanced_url: str = (
        f"https://www.basketball-reference.com/teams/{team_codes[team]}/{season}/gamelog-advanced/"
    )

    # Fetching the pages
    with Progress() as progress:
        task: int = progress.add_task("[cyan]Fetching pages...", total=2)
        basic_page: requests.models.Response = requests.get(basic_url)
        progress.advance(task)
        time.sleep(3)
        advanced_page: requests.models.Response = requests.get(advanced_url)
        progress.advance(task)
        time.sleep(3)
    # Souping the pages
    console.print("[bold cyan]Souping the fetched pages...[/bold cyan]")
    basic_soup: bs4.BeautifulSoup = bs4.BeautifulSoup(basic_page.content, "html.parser")
    advanced_soup: bs4.BeautifulSoup = bs4.BeautifulSoup(
        advanced_page.content, "html.parser"
    )

    # Grouping the basic and advanced stats
    console.print("[bold cyan]Extracting and parsing game logs...[/bold cyan]")
    basic_logs: list[bs4.element.Tag] = basic_soup.find_all(
        "tr", {"id": lambda x: x and x.startswith("team_game_log_reg.")}
    )
    advanced_logs: list[bs4.element.Tag] = advanced_soup.find_all(
        "tr", {"id": lambda x: x and x.startswith("team_game_log_adv_reg.")}
    )

    # Storing stats by game date
    stats = defaultdict(lambda: {"stats": {}, "average_stats": {}})
    with Progress() as progress:
        task: int = progress.add_task(
            "[cyan]Processing basic stats...", total=len(basic_logs)
        )
        for log in basic_logs:
            date: str = log.find("td", {"data-stat": "date"}).text
            stats[date]["stats"] = {
                "pts": int(log.find("td", {"data-stat": "team_game_score"}).text),
                "fg": int(log.find("td", {"data-stat": "fg"}).text),
                "fga": int(log.find("td", {"data-stat": "fga"}).text),
                "fg_pct": float(log.find("td", {"data-stat": "fg_pct"}).text),
                "fg3": int(log.find("td", {"data-stat": "fg3"}).text),
                "fg3a": int(log.find("td", {"data-stat": "fg3a"}).text),
                "fg3_pct": float(log.find("td", {"data-stat": "fg3_pct"}).text),
                "fg2": int(log.find("td", {"data-stat": "fg2"}).text),
                "fg2a": int(log.find("td", {"data-stat": "fg2a"}).text),
                "fg2_pct": float(log.find("td", {"data-stat": "fg2_pct"}).text),
                "ft": int(log.find("td", {"data-stat": "ft"}).text),
                "fta": int(log.find("td", {"data-stat": "fta"}).text),
                "ft_pct": float(log.find("td", {"data-stat": "ft_pct"}).text),
                "orb": int(log.find("td", {"data-stat": "orb"}).text),
                "drb": int(log.find("td", {"data-stat": "drb"}).text),
                "trb": int(log.find("td", {"data-stat": "trb"}).text),
                "ast": int(log.find("td", {"data-stat": "ast"}).text),
                "stl": int(log.find("td", {"data-stat": "stl"}).text),
                "blk": int(log.find("td", {"data-stat": "blk"}).text),
                "tov": int(log.find("td", {"data-stat": "tov"}).text),
                "pf": int(log.find("td", {"data-stat": "pf"}).text),
            }
            progress.advance(task)
        task: int = progress.add_task(
            "[cyan]Processing advanced stats...", total=len(advanced_logs)
        )
        for log in advanced_logs:
            date: str = log.find("td", {"data-stat": "date"}).text
            stats[date]["stats"].update(
                {
                    "ortg": float(log.find("td", {"data-stat": "team_off_rtg"}).text),
                    "drtg": float(log.find("td", {"data-stat": "team_def_rtg"}).text),
                    "pace": float(log.find("td", {"data-stat": "pace"}).text),
                    "ftr": float(log.find("td", {"data-stat": "fta_per_fga_pct"}).text),
                    "3ptar": float(
                        log.find("td", {"data-stat": "fg3a_per_fga_pct"}).text
                    ),
                    "ts": float(log.find("td", {"data-stat": "ts_pct"}).text),
                    "trb_pct": float(
                        log.find("td", {"data-stat": "team_trb_pct"}).text
                    ),
                    "ast_pct": float(
                        log.find("td", {"data-stat": "team_ast_pct"}).text
                    ),
                    "stl_pct": float(
                        log.find("td", {"data-stat": "team_stl_pct"}).text
                    ),
                    "blk_pct": float(
                        log.find("td", {"data-stat": "team_blk_pct"}).text
                    ),
                    "efg_pct": float(log.find("td", {"data-stat": "efg_pct"}).text),
                    "tov_pct": float(
                        log.find("td", {"data-stat": "team_tov_pct"}).text
                    ),
                    "orb_pct": float(
                        log.find("td", {"data-stat": "team_orb_pct"}).text
                    ),
                    "ft_rate": float(log.find("td", {"data-stat": "ft_rate"}).text),
                }
            )
            progress.advance(task)

    # Sorting dates for chronological processing
    game_dates: list[str] = sorted(stats.keys())

    # Calculating rolling averages for each game
    console.print("[bold green]Calculating rolling averages...[/bold green]")
    with Progress() as progress:
        task: int = progress.add_task(
            "[cyan]Processing rolling averages...", total=len(stats)
        )
        for i, date in enumerate(game_dates):
            past_games: list[str] = game_dates[max(0, i - 10) : i]

            for stat_key in stats[date]["stats"]:

                # Weights: most recent game has highest weight
                weights = list(range(1, len(past_games) + 1))  # e.g., [1, 2, 3,..., n]
                total_weight = sum(weights)

                # Weighted sum of the stats for the past games
                weighted_sum = sum(
                    stats[d]["stats"][stat_key] * weights[j]
                    for j, d in enumerate(past_games)
                )

                # Calculating weighted average
                avg_value: float = (
                    weighted_sum / total_weight
                    if total_weight
                    else stats[date]["stats"][stat_key]
                )

                # Storing the weighted average rounded to 2 decimal places
                stats[date]["average_stats"][stat_key] = round(avg_value, 2)
            progress.advance(task)

    console.print(
        f"[bold green]Data fetching complete for {team} - {season}![/bold green]"
    )
    return stats


# Fetch current month games schedule
def fetch_month_schedule(year: str, filename: str = "./csv/schedule.csv") -> None:

    # Getting the current month in lowercase
    month: datetime.datetime = datetime.datetime.now().strftime("%B").lower()

    # Constructing the URL to fetch
    url: str = (
        f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
    )

    # Requesting and souping the page
    page: requests.models.Response = requests.get(url)
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(page.content, "html.parser")

    # Filtering the schedules
    rows: list[bs4.element.Tag] = soup.find("tbody").find_all("tr")
    games: list[dict[str, str]] = list()
    for row in rows:
        if row.find("td", {"data-stat": "game_remarks"}).text != "":
            break
        game: dict[str, str] = dict()
        game["date"] = datetime.datetime.strptime(
            row.find("th", {"data-stat": "date_game"}).text, "%a, %b %d, %Y"
        ).strftime("%Y-%m-%d")
        game["home_team"] = row.find("td", {"data-stat": "home_team_name"}).text
        game["away_team"] = row.find("td", {"data-stat": "visitor_team_name"}).text
        games.append(game)

    # Read existing data to check for duplicates
    existing_rows: set = set()
    with open(filename, "r", newline="") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            existing_rows.add((row["date"], row["home_team"], row["away_team"]))

    # Filter out rows that already exist
    filtered_data: list[dict[str, str]] = [
        row
        for row in games
        if (row["date"], row["home_team"], row["away_team"]) not in existing_rows
    ]

    # Append only new rows
    if filtered_data:
        with open(filename, "a", newline="") as file:
            writer: csv.DictWriter = csv.DictWriter(
                file, fieldnames=["date", "home_team", "away_team"]
            )
            writer.writerows(filtered_data)
        console.print(
            f"[bold green]Appended {len(filtered_data)} new rows.[/bold green]"
        )
    else:
        console.print(
            "[bold purple]No new rows to append; all data already exists.[/bold purple]"
        )


# Saves the fetched team stats into a CSV file without overwriting existing data,
# ensuring the format remains consistent and duplicates are avoided.
def save_team_stats_to_csv(stats: dict, team: str, file_path: str) -> None:

    # Define expected columns
    columns: list[str] = [
        "date",
        "team",
        "pts",
        "fg",
        "fga",
        "fg_pct",
        "fg3",
        "fg3a",
        "fg3_pct",
        "fg2",
        "fg2a",
        "fg2_pct",
        "ft",
        "fta",
        "ft_pct",
        "orb",
        "drb",
        "trb",
        "ast",
        "stl",
        "blk",
        "tov",
        "pf",
        "ortg",
        "drtg",
        "pace",
        "ftr",
        "3ptar",
        "ts",
        "trb_pct",
        "ast_pct",
        "stl_pct",
        "blk_pct",
        "efg_pct",
        "tov_pct",
        "orb_pct",
        "ft_rate",
    ]

    # Convert stats dictionary into a DataFrame
    rows: list = list()
    for date, data in stats.items():
        row = {"date": date, "team": team}
        row.update(data["stats"])  # Add raw stats
        rows.append(row)

    new_data = pd.DataFrame(rows)

    # Ensure all required columns exist and fill missing ones with NaN
    new_data = new_data.reindex(columns=columns, fill_value=None)

    # Check if file exists
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)

        # Ensure column consistency
        existing_data = existing_data.reindex(columns=columns, fill_value=None)

        # Remove duplicates based on team and date
        combined_data = pd.concat([existing_data, new_data]).drop_duplicates(
            subset=["date", "team"], keep="first"
        )
    else:
        combined_data = new_data  # No existing data, write new data

    # Save to CSV
    combined_data.to_csv(file_path, index=False)
    console.print(f"[bold green]Stats saved to {file_path} successfully![/bold green]")


# Format a given csv schedule string and put it in a specific .csv file
def format_csv(input_csv: str, output_file: str) -> None:

    # Split the input CSV string into rows
    rows: list[str] = input_csv.strip().split("\n")

    # Create a CSV reader to process the input
    reader: csv.reader = csv.reader(rows)

    # Skip the header row
    next(reader)

    # Open the output CSV file in append mode
    with open(output_file, mode="a", newline="") as file:
        writer: csv.writer = csv.writer(file)

        # Process each row in the input CSV
        for row in reader:
            # Parse the relevant columns: Date, Home Team, Away Team, PTS (Home and Away)
            date_str: str = row[0]
            home_team: str = row[4]
            away_team: str = row[2]
            home_pts: str = int(row[5])
            away_pts: str = int(row[3])

            # Determine the winning team (0 for home, 1 for away)
            winning_team = 0 if home_pts > away_pts else 1

            # Convert the date string to the desired format
            date: str = datetime.datetime.strptime(date_str, "%a %b %d %Y").strftime(
                "%Y-%m-%d"
            )

            # Write the formatted data to the output file
            writer.writerow([date, home_team, away_team, winning_team])


# Sort the dataframe for better organization
def sort_csv() -> None:

    # Read the CSV file into a DataFrame
    df: pd.DataFrame = pd.read_csv("./csv/gamelogs.csv")

    # Ensure date column is treated as datetime for sorting
    df["date"] = pd.to_datetime(df["date"])

    # Sort by home_team (A-Z) first, then by date
    df: pd.DataFrame = df.sort_values(by=["team", "date"])

    # Convert the date column back to its original format (YYYY-MM-DD)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Save the sorted DataFrame back to a CSV file
    df.to_csv("./csv/gamelogs.csv", index=False)


if __name__ == "__main__":
    target_year: str = "2025"
    command: str = console.input(
        "[bold blue]Fetch games' logs (1) - Fetch calendar (2) -> [/bold blue]"
    )
    if command == "1":
        for team in team_codes.keys():
            save_team_stats_to_csv(
                fetch_team_season_log(team, target_year), team, "csv/gamelogs.csv"
            )
        sort_csv()
    elif command == "2":
        fetch_month_schedule(target_year)
