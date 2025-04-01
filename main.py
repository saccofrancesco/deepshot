# Importing libraries
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
importance_scores: np.ndarray = model.feature_importances_

# Sort feature indices by importance (descending order)
sorted_indices: np.ndarray = np.argsort(importance_scores)[::-1]

# Extract feature names while ensuring uniqueness
unique_stats: list = list()
for i in sorted_indices:
    stat_name: str = (
        model.feature_names_in_[i].replace("home_", "").replace("away_", "")
    )
    if stat_name not in unique_stats:
        unique_stats.append(stat_name)
    if len(unique_stats) == 15:  # Stop once we have 15 unique stats
        break

stats_tags: list[str] = unique_stats  # Top 15 most important unique stat names

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
    "tov_pct": "Turnover % (TOV%)",
    "orb_pct": "Offensive Rebound % (ORB%)",
    "ft_rate": "Free Throws Per Field Goal Attempt (FT/FGA)",
    "poss": "Possessions (POSS)",
    "usg_pct": "Usage % (USG%)",
    "tov_to_poss": "Turnover-to-Possesion Ratio (TOV/POSS)",
    "ft_to_poss": "Free Throw per Possesion (FT/POSS),"
}

# Storing stats that if lower are better:
lower_better_stats: set = {"tov", "pf", "drtg", "tov_pct", "tov_to_poss"}

# Get the next day NBA game
year: datetime.datetime = datetime.datetime.now().strftime("%Y")
today: datetime.datetime = datetime.datetime.now().strftime(f"{year}-%m-%d")


# Function to retrieve and get the scheduled games for today
def extract_games(date: str) -> list[dict[str, str | int | float]]:

    games: list = list()

    with open("./data/csv/schedule.csv", "r", newline="") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            if row["date"] == date:
                games.append(
                    {"home_team": row["home_team"], "away_team": row["away_team"]}
                )

    return games


# Search the last available stat for each team and append it as home and away
@lru_cache(maxsize=128)
# Search the last available stat for each team and append it as home and away
def find_most_recent_stats(
    team_name: str, file_path: str = "./data/csv/averages.csv"
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


# Creating the Card UI
class GameCard(ui.card):
    def __init__(self, game: dict[str, str | int | float]) -> None:

        # Initializing the super class
        super().__init__()
        self.classes("m-4 p-8 rounded-2xl shadow-md border w-[650px]")

        # Arranging the info
        with self:

            # Row for Team Logos and "VS"
            with ui.row().classes("items-center justify-between w-full mb-2"):
                ui.image(f"./img/badges/{game['home_team']}.png").classes("w-32")
                ui.label("VS").classes("text-lg font-semibold text-center w-20")
                ui.image(f"./img/badges/{game['away_team']}.png").classes("w-32")

            # Row for Team Names and Win Probabilities
            with ui.row().classes("items-center justify-between w-full mb-2"):
                with ui.column().classes("items-start"):
                    ui.label(game["home_team"]).classes("text-left text-md font-bold")
                    ui.label(f"Win Prob: {game['home_prob']} %").classes(
                        f"text-left text-md font-bold {'text-green-600' if game['home_prob'] > 50 else 'text-red-600'}"
                    )

                with ui.column().classes("items-end"):
                    ui.label(game["away_team"]).classes("text-right text-md font-bold")
                    ui.label(f"Win Prob: {game['away_prob']} %").classes(
                        f"text-right text-md font-bold {'text-green-600' if game['away_prob'] > 50 else 'text-red-600'}"
                    )

            # Wide & Rounded "See More" Expansion
            with ui.expansion().classes(
                "w-full shadow-md bg-gray-100 rounded-2xl overflow-hidden mx-auto"
            ).props("duration=550 hide-expand-icon") as expansion:

                # Toggle the label on / off based on the expansion state
                def toggle_label() -> None:
                    label.set_text(
                        "Click to hide" if expansion.value else "Click for more"
                    )
                    icon.set_name("expand_less" if expansion.value else "expand_more")

                expansion.on(
                    "update:model-value", toggle_label
                )  # Listen for expansion state changes

                with expansion.add_slot("header"):
                    with ui.row().classes("w-full justify-center items-center"):
                        label: ui.label = ui.label("Click for more").classes(
                            "text-md font-bold text-center"
                        )
                        icon: ui.icon = ui.icon("expand_more").classes("text-xl")

                # Expanded Stats Section
                with ui.row().classes("w-full"):

                    # Home team stats
                    with ui.column().classes("items-start flex-1"):
                        for stat in stats_tags:
                            home_val: str = float(game[f"home_{stat}"])
                            away_val: str = float(game[f"away_{stat}"])
                            diff: float = (
                                abs(home_val - away_val) / max(home_val, away_val) * 100
                            )

                            # Determine if the stat is "better" when lower
                            is_lower_better: bool = stat in lower_better_stats

                            if (
                                diff >= 5
                            ):  # Apply coloring only when the difference is at least 5%
                                if (home_val > away_val and not is_lower_better) or (
                                    home_val < away_val and is_lower_better
                                ):
                                    style: str = (
                                        "text-green-600 font-bold"  # Home team has better stat
                                    )
                                else:
                                    style: str = (
                                        "text-red-600 font-bold"  # Home team has worse stat
                                    )
                            else:
                                style: str = "text-black"

                            ui.label(game[f"home_{stat}"]).classes(
                                f"text-left text-sm {style}"
                            )

                    # Stat labels (Centered)
                    with ui.column().classes("items-center flex-2"):
                        for stat in stats_tags:
                            ui.label(stat_to_full_name_desc[stat]).classes(
                                "text-center text-sm font-bold"
                            )

                    # Away team stats
                    with ui.column().classes("items-end flex-1"):
                        for stat in stats_tags:
                            home_val: str = float(game[f"home_{stat}"])
                            away_val: str = float(game[f"away_{stat}"])
                            diff: float = (
                                abs(home_val - away_val) / max(home_val, away_val) * 100
                            )

                            # Determine if the stat is "better" when lower
                            is_lower_better: bool = stat in lower_better_stats

                            if diff >= 5:
                                if (away_val > home_val and not is_lower_better) or (
                                    away_val < home_val and is_lower_better
                                ):
                                    style: str = (
                                        "text-green-600 font-bold"  # Away team has better stat
                                    )
                                else:
                                    style: str = (
                                        "text-red-600 font-bold"  # Away team has worse stat
                                    )
                            else:
                                style: str = "text-black"

                            ui.label(game[f"away_{stat}"]).classes(
                                f"text-right text-sm {style}"
                            )


# Creating the game list UI
class GameList:
    def __init__(self, date: str) -> None:

        # Storing the date to render the cards
        self.date: str = date

    # Render all the cards
    @ui.refreshable
    def render(self) -> None:

        # For each game shcedule for today date, extract the home team and away team
        try:
            games: list[dict[str, str | int | float]] = list()
            for game in extract_games(self.date):
                stat_label, stats = find_most_recent_stats(game["home_team"])
                for i, _ in enumerate(stat_label):
                    game[f"home_{stat_label[i]}"] = stats[i]
                stat_label, stats = find_most_recent_stats(game["away_team"])
                for i, _ in enumerate(stat_label):
                    game[f"away_{stat_label[i]}"] = stats[i]
                games.append(game)

            # Convert data into DataFrame
            df: pd.DataFrame = pd.DataFrame(games)

            # Drop non-numeric columns (team names)
            df: pd.DataFrame = df.drop(["home_team", "away_team"], axis=1)

            # Drop irrelvant stats columns
            stats_to_drop: list[str] = []
            for stat in stats_to_drop:
                df: pd.DataFrame = df.drop([f"home_{stat}", f"away_{stat}"], axis=1)

            # Convert all values to float (they are strings in the provided data)
            df: pd.DataFrame = df.astype(float)

            # Make predictions
            predictions: list[int] = model.predict(df)

            # Get probabilities
            prob: list[list[float]] = model.predict_proba(df)

            # Appending the new data to the games dict
            for i, game in enumerate(games):
                game["winner"] = (
                    game["home_team"] if predictions[i] == 0 else game["away_team"]
                )
                game["home_prob"] = round(float(prob[i][0]) * 100, 2)
                game["away_prob"] = round(float(prob[i][1]) * 100, 2)

            # After clearing the container, rendering the game cards
            for game in games:
                GameCard(game)
        except:
            pass


# Add custom CSS to remove unwanted borders and padding
ui.add_css(".nicegui-content { margin: 0; padding: 0; height: 100%; }")
ui.add_css(".nicegui-content { height: 100%; }")
ui.add_css(".w-1/3, .w-2/3 { border: none; box-shadow: none; }")

# Main app logic
with ui.element("div").classes("w-full h-full flex"):

    # Creating the 2 containers
    with ui.element("div").classes(
        "w-1/3 flex justify-center items-center fixed h-full bg-blue"
    ):
        date_container: ui.element = ui.element("div")

    with ui.element("div").classes("w-2/3 ml-auto h-full overflow-auto bg-red p-16"):
        cards_container: ui.element = ui.element("div")

    # Rendering the games list
    with cards_container:
        games_list: GameList = GameList(today)
        with ui.column(align_items="center"):
            games_list.render()

    # Creating the date picker
    with date_container:
        with ui.column(align_items="center"):
            date: ui.date = (
                ui.date(today)
                .bind_value_to(games_list, "date")
                .props("color=black")
                .style("border-radius: 16px;")
            )

            predict_button: ui.button = (
                ui.button("Predict", on_click=games_list.render.refresh)
                .props("rounded push size=lg color=black")
                .classes("rounded-2xl mt-4")
            )


# Running the app
ui.run(title="Deepshot AI")
