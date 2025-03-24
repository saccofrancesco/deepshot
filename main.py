# Importing libraries
import requests
import bs4
import datetime
import csv
import pandas as pd
import joblib
import sklearn.ensemble
import numpy as np
from nicegui import ui
from functools import lru_cache

# Loading the model
model: sklearn.ensemble._forest.RandomForestClassifier = joblib.load(
    "./model/deepshot.pkl"
)

# Get feature importance scores
importance_scores = model.feature_importances_

# Sort feature indices by importance (descending order)
sorted_indices = np.argsort(importance_scores)[::-1]

# Extract feature names while ensuring uniqueness
unique_stats = []
for i in sorted_indices:
    stat_name = model.feature_names_in_[i].replace("home_", "").replace("away_", "")
    if stat_name not in unique_stats:
        unique_stats.append(stat_name)
    if len(unique_stats) == 15:  # Stop once we have 10 unique stats
        break

stats_tags = unique_stats  # Top 10 most important unique stat names

# Stats -> Full description dict
stat_to_full_name_desc: dict[str, str] = {
    "pts": "Points Per Game (PPG)",
    "fg": "Field Goals (FG)",
    "fga": "Field Goal Attempts (FGA)",
    "fg_pct": "Field Goal % (FG%)",
    "fg3": "3-Point Field Goals (3P)",
    "fg3a": "3-Point Field Goal Attempts (3PA)",
    "fg3_pct": "3-Point Field Goal % (3P%)",
    "fg2": "2-Point Field Goals (2P)",
    "fg2a": "2-Point Field Goal Attempts (2PA)",
    "fg2_pct": "2-Point Field Goal % (2P%)",
    "ft": "Free Throws (FT)",
    "fta": "Free Throw Attempts (FTA)",
    "ft_pct": "Free Throw % (FT%)",
    "orb": "Offensive Rebounds (ORB)",
    "drb": "Defensive Rebounds (DRB)",
    "trb": "Total Rebounds (TRB)",
    "ast": "Assists (AST)",
    "stl": "Steals (STL)",
    "blk": "Blocks (BLK)",
    "tov": "Turnovers (TOV)",
    "pf": "Personal Fouls (PF)",
    "ortg": "Offensive Rating (ORtg)",
    "drtg": "Defensive Rating (DRtg)",
    "pace": "Pace",
    "ftr": "Free Throw Attempt Rate (FTr)",
    "3ptar": "3-Point Attempt Rate (3PAr)",
    "ts": "True Shooting % (TS%)",
    "trb_pct": "Total Rebound % (TRB%)",
    "ast_pct": "Assist % (AST%)",
    "stl_pct": "Steal % (STL%)",
    "blk_pct": "Block % (BLK%)",
    "efg_pct": "Effective Field Goal % (eFG%)",
    "tov_pct": "Turnover %",
    "orb_pct": "Offensive Rebound %",
    "ft_rate": "Free Throws Per Field Goal Attempt",
}


# Get the next day NBA game
month: datetime.datetime = datetime.datetime.now().strftime("%B").lower()
year: datetime.datetime = datetime.datetime.now().strftime("%Y")
today: datetime.datetime = datetime.datetime.now().strftime(f"{year}-%m-%d")


# Function to fetch and get the scheduled games for today
@lru_cache(maxsize=None)
def fetch_todays_games(year: str, month: str) -> list[dict[str, str | int | float]]:

    # Composing the schedule URL
    schedule_url: str = (
        f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
    )

    # Requesting and souping the schedule page
    page: requests.models.Response = requests.get(schedule_url)
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(page.content, "html.parser")

    # Filtering the schedules
    rows: list[bs4.element.Tag] = soup.find("tbody").find_all("tr")
    daily_game_rows: list[bs4.element.Tag] = list()
    for row in rows:
        if date := row.find("th", {"data-stat": "date_game"}).text:
            if (
                datetime.datetime.strptime(date, "%a, %b %d, %Y").strftime("%Y-%m-%d")
                == "2025-03-24"
            ):
                daily_game_rows.append(row)

    return daily_game_rows


# Search the last available stat for each team and append it as home and away
def find_most_recent_stats(
    team_name: str, file_path: str = "./data/csv/rolling_averages.csv"
) -> tuple[str, str]:
    most_recent_row = None
    most_recent_date = None

    with open(file_path, mode="r", newline="") as file:
        reader: csv.reader = csv.reader(file)

        # Read the headers
        headers: list[str] = next(reader)

        for row in reader:
            date_str, team = row[0], row[1]

            if team == team_name:
                current_date: str = datetime.datetime.strptime(date_str, "%Y-%m-%d")

                if most_recent_date is None or current_date > most_recent_date:
                    most_recent_date: str = current_date
                    most_recent_row: str = row

    if most_recent_row:
        return headers[2:], most_recent_row[2:]
    else:
        return None, None


# For each game shcedule for today date, extract the home team and away team
games: list[dict[str, str | int | float]] = list()
for game in fetch_todays_games(year, month):
    matchup: dict[str, str | int | float] = {
        "home_team": game.find("td", {"data-stat": "home_team_name"}).text,
        "away_team": game.find("td", {"data-stat": "visitor_team_name"}).text,
    }
    stat_label, stats = find_most_recent_stats(matchup["home_team"])
    for i, _ in enumerate(stat_label):
        matchup[f"home_{stat_label[i]}"] = stats[i]
    stat_label, stats = find_most_recent_stats(matchup["away_team"])
    for i, _ in enumerate(stat_label):
        matchup[f"away_{stat_label[i]}"] = stats[i]
    games.append(matchup)

# Convert data into DataFrame
df: pd.DataFrame = pd.DataFrame(games)

# Drop non-numeric columns (team names)
df: pd.DataFrame = df.drop(["home_team", "away_team"], axis=1)

# Convert all values to float (they are strings in the provided data)
df: pd.DataFrame = df.astype(float)

# Make predictions
predictions: list[int] = model.predict(df)

# Get probabilities
prob: list[list[float]] = model.predict_proba(df)

# Appending the new data to the games dict
for i, game in enumerate(games):
    game["winner"] = game["home_team"] if predictions[i] == 0 else game["away_team"]
    game["home_prob"] = round(float(prob[i][0]) * 100, 2)
    game["away_prob"] = round(float(prob[i][1]) * 100, 2)


# Creating a default card component to use feeding into it the game data, for each game
def game_card(game: dict[str, str]) -> ui.card:
    card: ui.card = ui.card().classes("m-4 p-4 rounded-2xl shadow-md border")
    with card:
        with ui.expansion().style("width: 800px;") as expansion:
            with expansion.add_slot("header"):
                with ui.row().style("width: 750px;").classes(
                    "items-center justify-between gap-4"
                ):

                    # Home team (Left-Aligned)
                    with ui.column().classes("items-start w-1/3"):
                        ui.image(f"./img/badges/{game['home_team']}.png").classes(
                            "w-36"
                        )
                        ui.label(game["home_team"]).classes(
                            "text-left text-md font-bold"
                        )
                        ui.label(f"Win Prob: {game['home_prob']} %").classes(
                            f"text-left text-md font-bold {'text-green-600' if game['home_prob'] > 50 else 'text-red-600'}"
                        )

                    # Centered "VS"
                    ui.label("VS").classes("text-lg font-semibold").style(
                        "min-width: 80px; text-align: center;"
                    )

                    # Away team (Right-Aligned)
                    with ui.column().classes("items-end w-1/3"):
                        ui.image(f"./img/badges/{game['away_team']}.png").classes(
                            "w-36z"
                        )
                        ui.label(game["away_team"]).classes(
                            "text-right text-md font-bold"
                        )
                        ui.label(f"Win Prob: {game['away_prob']} %").classes(
                            f"text-right text-md font-bold {'text-green-600' if game['away_prob'] > 50 else 'text-red-600'}"
                        )

            # Expanded Stats Section (Smaller Text)
            with ui.row().style("width: 750px;").classes("w-full"):

                # Home team stats (Left-Aligned)
                with ui.column().classes("items-start flex-1"):
                    for stat in stats_tags:
                        home_val = float(game[f"home_{stat}"])
                        away_val = float(game[f"away_{stat}"])
                        diff = abs(home_val - away_val) / max(home_val, away_val) * 100

                        style = (
                            "text-green-600 font-bold"
                            if home_val > away_val and diff >= 5
                            else (
                                "text-red-600 font-bold"
                                if home_val < away_val and diff >= 5
                                else "text-black"
                            )
                        )

                        ui.label(game[f"home_{stat}"]).classes(
                            f"text-left text-sm {style}"
                        )

                # Stat labels (Centered)
                with ui.column().classes("items-center flex-1"):
                    for stat in stats_tags:
                        ui.label(stat_to_full_name_desc[stat]).classes(
                            "text-center text-sm font-bold"
                        )

                # Away team stats (Right-Aligned)
                with ui.column().classes("items-end pr-6 flex-1"):
                    for stat in stats_tags:
                        home_val = float(game[f"home_{stat}"])
                        away_val = float(game[f"away_{stat}"])
                        diff = abs(home_val - away_val) / max(home_val, away_val) * 100

                        style = (
                            "text-green-600 font-bold"
                            if away_val > home_val and diff >= 5
                            else (
                                "text-red-600 font-bold"
                                if away_val < home_val and diff >= 5
                                else "text-black"
                            )
                        )

                        ui.label(game[f"away_{stat}"]).classes(
                            f"text-right text-sm {style}"
                        )

    return card


# Rendering the cards for each game
with ui.element("div").classes("p-8 flex justify-center items-center"):
    for game in games:
        game_card(game)

# Running the app
ui.run(title="Deepshot AI")
