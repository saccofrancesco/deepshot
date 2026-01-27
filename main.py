# Importing libraries
import datetime
import csv
import pandas as pd
import joblib
import sklearn.ensemble
import numpy as np
from nicegui import app, ui
from functools import lru_cache
from collections import defaultdict
from itertools import product
from colorsys import rgb_to_hsv
import json
from urllib.parse import quote, unquote
import traceback

# Adding static files (teams' logos)
app.add_static_files("./static", "static")

# Global dictionary to hold team stats
team_stats_data: defaultdict = defaultdict(list)
headers: list[str] = list()


# Load CSV once
def load_team_stats(file_path: str = "./data/csv/averages.csv"):
    """
    Load per-team statistics from a CSV file into memory for fast lookup.

    This function reads a CSV file containing team statistics, stores the
    header row in a global variable, and groups the remaining rows by team
    in a global data structure. Each team's data is sorted by date in
    descending order to allow efficient retrieval of the most recent
    available statistics.

    Parameters
    ----------
    file_path : str, optional
        Path to the CSV file containing team statistics.
        Defaults to "./data/csv/averages.csv".

    Returns
    -------
    None
        This function does not return a value. It populates global
        variables used elsewhere in the application.

    Raises
    ------
    FileNotFoundError
        If the specified CSV file does not exist.
    StopIteration
        If the CSV file is empty and no header row is found.
    OSError
        If the file cannot be opened or read.

    Notes
    -----
    - This function relies on and mutates global variables (`headers`,
      `team_stats_data`).
    - Team statistics are stored as `(date_str, row)` tuples.
    - Data is sorted in descending date order for fast access to recent games.
    """
    global headers
    with open(file_path, mode="r", newline="") as file:
        reader: csv.reader = csv.reader(file)
        headers = next(reader)  # store headers

        for row in reader:
            date_str, team = row[0], row[1]
            team_stats_data[team].append((date_str, row))

    # Sort each team’s data by date descending for quick retrieval
    for team in team_stats_data:
        team_stats_data[team].sort(reverse=True)


# Call once at startup
load_team_stats()

# Loading the model
model: sklearn.ensemble._forest.RandomForestClassifier = joblib.load(
    "./model/deepshot.pkl"
)

# Get feature importance scores
importance_scores: np.ndarray = model.feature_importances_

# Sort feature indices by importance (descending order)
sorted_indices: np.ndarray = np.argsort(importance_scores)[::-1]

# Extract feature names while ensuring uniqueness
unique_stats: list[str] = list()
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
    "pace": "Pace (Possessions per 48 minutes)",
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
    "ast_tov": "Assist-to-Turnover (AST/TOV)",
    "ast_ratio": "Assist Ratio (ASTr)",
    "elo": "ELO Rating",
}

# Teams color codes list
team_color_codes: dict[str, list[str]] = {
    "Atlanta Hawks": ["#e03a3e", "#c1d32f"],
    "Boston Celtics": ["#007a33", "#ba9653", "#963821"],
    "Brooklyn Nets": ["#000000"],
    "Charlotte Hornets": ["#1d1160", "#00788c"],
    "Chicago Bulls": ["#ce1141"],
    "Cleveland Cavaliers": ["#860038", "#fdbb30"],
    "Dallas Mavericks": ["#00538c", "#002b5e"],
    "Denver Nuggets": ["#0e2240", "#fec524", "#8b2131", "#1d428a"],
    "Detroit Pistons": ["#c8102e", "#1d42ba", "#002d62"],
    "Golden State Warriors": ["#1d428a", "#ffc72c"],
    "Houston Rockets": ["#ce1141"],
    "Indiana Pacers": ["#002d62", "#fdbb30"],
    "Los Angeles Clippers": ["#c8102e", "#1d428a"],
    "Los Angeles Lakers": ["#552583", "#f9a01b"],
    "Memphis Grizzlies": ["#5d76a9", "#12173f", "#f5b112"],
    "Miami Heat": ["#98002e", "#f9a01b"],
    "Milwaukee Bucks": ["#00471b", "#0077c0"],
    "Minnesota Timberwolves": ["#0c2340", "#236192", "#78be20"],
    "New Orleans Pelicans": ["#0c2340", "#c8102e", "#85714d"],
    "New York Knicks": ["#006bb6", "#f58426"],
    "Oklahoma City Thunder": ["#007ac1", "#ef3b24", "#002d62"],
    "Orlando Magic": ["#0077c0"],
    "Philadelphia 76ers": ["#006bb6", "#ed174c", "#002b5c"],
    "Phoenix Suns": ["#1d1160", "#e56020", "#ffcd00", "#b95915"],
    "Portland Trail Blazers": ["#e03a3e"],
    "Sacramento Kings": ["#5a2d81", "#63727a"],
    "San Antonio Spurs": ["#c4ced4", "#000000"],
    "Toronto Raptors": ["#ce1141", "#b4975a"],
    "Utah Jazz": ["#753bbd"],
    "Washington Wizards": ["#002b5c", "#e31837"],
}


# Function to get the best colors from a set of two list mapped by two team names
def get_best_color_pair(team1: str, team2: str) -> tuple[str, str]:
    """
    Select the most visually contrasting color pair for two teams.

    This function compares all possible color combinations between two teams
    and returns the pair with the highest visual contrast. Contrast is
    approximated using differences in saturation and value (brightness)
    in HSV color space.

    Team colors are retrieved from a predefined mapping of team names
    to lists of hex color codes.

    Parameters
    ----------
    team1 : str
        Name of the first team.
    team2 : str
        Name of the second team.

    Returns
    -------
    tuple[str, str]
        A tuple containing the selected hex color codes
        `(team1_color, team2_color)` with the highest contrast.

    Raises
    ------
    ValueError
        If one or both team names are not found in the color mapping
        or do not have associated colors.

    Notes
    -----
    - Hex colors are converted to HSV for contrast evaluation.
    - Contrast is defined as the sum of absolute differences in
      saturation and value components.
    - Hue is not considered, prioritizing brightness and intensity
      differences for better readability.
    - This function assumes `team_color_codes` is defined in the
      enclosing scope.
    """

    # Convert the hex color code in to rgb
    def hex_to_hsv(hex_color: str) -> tuple:
        hex_color: str = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        return rgb_to_hsv(r, g, b)

    # Get the mapped colors
    colors_team1: str = team_color_codes.get(team1, [])
    colors_team2: str = team_color_codes.get(team2, [])

    if not colors_team1 or not colors_team2:
        raise ValueError("Invalid team names provided.")

    best_pair = None
    max_contrast: int = -1

    # Extract the contrast for each combination
    for color1, color2 in product(colors_team1, colors_team2):
        _, s1, v1 = hex_to_hsv(color1)
        _, s2, v2 = hex_to_hsv(color2)
        contrast: float = abs(v1 - v2) + abs(s1 - s2)

        # If the current contrast is > than the one before, those will be the new colors
        # and the contrast will be the threshold
        if contrast > max_contrast:
            max_contrast: float = contrast
            best_pair: tuple[str, str] = (color1, color2)

    return best_pair


# Storing stats that if lower are better:
lower_better_stats: set = {"tov", "pf", "drtg", "tov_pct", "tov_to_poss"}

# Get the next day NBA game
year: datetime.datetime = datetime.datetime.now().strftime("%Y")
today: datetime.datetime = datetime.datetime.now().strftime(f"{year}-%m-%d")


# Function to retrieve and get the scheduled games for today
def extract_games(date: str) -> list[dict[str, str | int | float]]:
    """
    Retrieve all scheduled games for a specific date.

    This function reads the schedule CSV file and extracts the home and
    away teams for all games scheduled on the given date.

    Parameters
    ----------
    date : str
        Target date in `YYYY-MM-DD` format.

    Returns
    -------
    list[dict[str, str]]
        A list of dictionaries, each containing:
        - "home_team": name of the home team
        - "away_team": name of the away team

        Returns an empty list if no games are scheduled for the given date.

    Raises
    ------
    FileNotFoundError
        If the schedule CSV file cannot be found.
    KeyError
        If expected columns are missing from the CSV file.
    OSError
        If the file cannot be opened or read.

    Notes
    -----
    - The schedule is read from `./data/csv/schedule.csv`.
    - No date parsing is performed; the comparison is string-based.
    """
    games: list[dict[str, str | int | float]] = list()
    with open("./data/csv/schedule.csv", "r", newline="") as file:
        reader: csv.DictReader = csv.DictReader(file)
        for row in reader:
            if row["date"] == date:
                games.append(
                    {"home_team": row["home_team"], "away_team": row["away_team"]}
                )
    return games


@lru_cache(maxsize=128)
def find_most_recent_stats(
    team_name: str, target_date: str
) -> tuple[list[str], list[str]]:
    """
    Retrieve the most recent available statistics for a team before a given date.

    This function searches cached, in-memory team statistics and returns the
    latest statistics entry that occurred strictly before the specified
    target date. Results are memoized using an LRU cache to speed up repeated
    lookups for the same team and date.

    Parameters
    ----------
    team_name : str
        Name of the team whose statistics are requested.
    target_date : str
        Cutoff date in `YYYY-MM-DD` format. Only statistics recorded
        before this date are considered.

    Returns
    -------
    tuple[list[str], list[str]]
        A tuple containing:
        - A list of statistic column names
        - A list of corresponding statistic values

        Returns `(None, None)` if the team is not found or no prior
        statistics exist for the given date.

    Notes
    -----
    - Date comparison is performed lexicographically and assumes
      `YYYY-MM-DD` formatting.
    - The returned columns and values exclude the `date` and `team`
      fields.
    - This function relies on globally loaded data structures
      (`team_stats_data`, `headers`).
    - Caching improves performance when querying multiple games
      on the same date.
    """
    if team_name not in team_stats_data:
        return (None, None)

    for date_str, row in team_stats_data[team_name]:
        if date_str < target_date:
            return (headers[2:], row[2:])  # Skip date and team name

    return (None, None)


# Creating the Card UI
class GameCard(ui.card):
    def __init__(self, game: dict[str, str | int | float], date: str) -> None:
        """
        UI card component displaying a scheduled NBA game and its analytics.

        This class renders an interactive card showing two teams facing each
        other on a given date, including team logos, win probabilities,
        color-coded probability bars, and an expandable section with detailed
        statistical comparisons.

        The card visually highlights statistical advantages using color cues
        and allows navigation to a detailed game view.

        Parameters
        ----------
        game : dict[str, str | int | float]
            Dictionary containing all game-related data, including:
            - team names
            - win probabilities
            - per-team statistics prefixed with `home_` and `away_`
        date : str
            Game date in `YYYY-MM-DD` format, used for routing and display.

        Notes
        -----
        - Team colors are dynamically selected to maximize visual contrast.
        - Win probability bars are scaled proportionally to predicted win chances.
        - Detailed stats are shown in an expandable section with conditional
          coloring based on relative performance.
        - This component depends on several globally defined utilities and
          mappings, including:
            - `get_best_color_pair`
            - `stats_tags`
            - `lower_better_stats`
            - `stat_to_full_name_desc`
        - Designed for use with NiceGUI (`ui.card`, `ui.row`, `ui.column`, etc.).
        """

        # Initializing the super class
        super().__init__()
        self.classes("m-4 p-10 rounded-2xl shadow-md border w-[650px]").style(
            "background-color: #e3e4e6;"
        )

        # Arranging the info
        with self:

            # Calculating the color for each team
            home_color, away_color = get_best_color_pair(
                game["home_team"], game["away_team"]
            )

            # Row for Team Logos and "VS"
            with ui.row(align_items="center").classes(
                "items-center justify-between w-full"
            ):
                ui.image(f"static/{game['home_team']}.png").classes("w-32")
                ui.image(f"static/vs.png").classes("w-16")
                ui.image(f"static/{game['away_team']}.png").classes("w-32")

            # Row for the info / details button
            with ui.row().classes("w-full flex justify-center items-center"):
                with ui.column().classes("items-center"):
                    ui.button(
                        "Details",
                        icon="info",
                        on_click=lambda: ui.navigate.to(
                            f"/{date}/{quote(json.dumps(game))}"
                        ),
                    ).props("unelevated rounded color=grey-2 text-color=grey-5")

            # Row for Team Names and Win Probabilities
            with ui.row(align_items="stretch").classes("justify-between w-full"):
                with ui.column(align_items="start"):
                    ui.label(game["home_team"]).classes("text-left text-lg font-bold")
                    ui.label(f"W {game['home_prob']} %").classes(
                        f"text-left text-lg font-bold"
                    )

                with ui.column(align_items="end"):
                    ui.label(game["away_team"]).classes("text-right text-lg font-bold")
                    ui.label(f"W {game['away_prob']} %").classes(
                        f"text-right text-lg font-bold"
                    )

            # HTML element to create W % bars
            with ui.element("div").classes("flex w-full h-6"):
                ui.element("div").style(
                    f"flex: {game['home_prob']}; background-color: {home_color}"
                ).classes("rounded-md mr-1")
                ui.element("div").style(
                    f"flex: {game['away_prob']}; background-color: {away_color}"
                ).classes("rounded-md ml-1")

            # Wide & Rounded "See More" Expansion toggle
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
                            home_val: float = float(game[f"home_{stat}"])
                            away_val: float = float(game[f"away_{stat}"])
                            diff: float = (
                                abs(home_val - away_val) / max(home_val, away_val) * 100
                            )

                            # Determine if the stat is "better" when lower
                            is_lower_better: bool = stat in lower_better_stats

                            if (
                                diff >= 3
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
                    with ui.column().classes("items-center flex-3.5"):
                        for stat in stats_tags:
                            ui.label(stat_to_full_name_desc[stat]).classes(
                                "text-center text-sm font-bold"
                            )

                    # Away team stats
                    with ui.column().classes("items-end flex-1"):
                        for stat in stats_tags:
                            home_val: float = float(game[f"home_{stat}"])
                            away_val: float = float(game[f"away_{stat}"])
                            diff: float = (
                                abs(home_val - away_val) / max(home_val, away_val) * 100
                            )

                            # Determine if the stat is "better" when lower
                            is_lower_better: bool = stat in lower_better_stats

                            if diff >= 3:
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
        """
        Controller class responsible for rendering game cards for a given date.

        This class retrieves scheduled games for a specific date, enriches them
        with the most recent available team statistics, runs model predictions
        to estimate game outcomes, and renders a `GameCard` UI component for
        each game.

        Parameters
        ----------
        date : str
            Target date in `YYYY-MM-DD` format for which games should be rendered.

        Notes
        -----
        - Team statistics are retrieved using cached historical data to avoid
          data leakage.
        - Predictions are generated using a pre-trained machine learning model.
        - This class orchestrates data extraction, feature preparation,
          prediction, and UI rendering.
        """

        # Storing the date to render the cards
        self.date: str = date

    # Render all the cards
    def render(self) -> None:
        """
        Render game cards for all scheduled games on the specified date.

        This method:
        - Retrieves scheduled games for the given date
        - Augments each game with the most recent team statistics
        - Prepares features and runs model predictions
        - Attaches win probabilities to each game
        - Instantiates a `GameCard` UI component for each game

        Returns
        -------
        None
            This method does not return a value. It renders UI components
            directly.

        Notes
        -----
        - Non-numeric columns are removed before prediction.
        - Feature values are cast to float prior to model inference.
        - Any exceptions during rendering are silently ignored.
        """

        # For each game shcedule for today date, extract the home team and away team
        try:
            games: list[dict[str, str | int | float]] = list()
            for game in extract_games(self.date):
                stat_label, stats = find_most_recent_stats(game["home_team"], self.date)
                for i, _ in enumerate(stat_label):
                    game[f"home_{stat_label[i]}"] = stats[i]
                stat_label, stats = find_most_recent_stats(game["away_team"], self.date)
                for i, _ in enumerate(stat_label):
                    game[f"away_{stat_label[i]}"] = stats[i]
                games.append(game)

            # Check if games is empty
            if not games:
                print("No games found for this date")
                return

            # Convert data into DataFrame
            df: pd.DataFrame = pd.DataFrame(games)

            # Drop non-numeric columns (team names)
            df: pd.DataFrame = df.drop(["home_team", "away_team"], axis=1)

            # Drop irrelvant stats columns
            stats_to_drop: list[str] = list()
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
                game["home_prob"] = round(float(prob[i][0]) * 100)
                game["away_prob"] = round(float(prob[i][1]) * 100)

            # After clearing the container, rendering the game cards
            for game in games:
                GameCard(game, self.date)

        except FileNotFoundError as e:
            print(f"Error: Could not find required files - {e}")
        except KeyError as e:
            print(f"Error: Missing expected data field - {e}")
        except ValueError as e:
            print(f"Error: Invalid data format - {e}")
        except Exception as e:
            print(f"Unexpected error during prediction: {e}")
            traceback.print_exc()


# Redirect to page
@ui.page("/")
def redirect() -> None:
    """
    Redirect the root page to the current day's games view.

    This page handler automatically navigates users from the application
    root URL to the page corresponding to today's date.

    Returns
    -------
    None
        This function does not return a value. It performs a client-side
        navigation using NiceGUI.
    """
    ui.navigate.to(today)


# Home day prediction and stats page template
@ui.page("/{date}")
def home(date: str) -> None:
    """
    Render the main home page for a specific date with game predictions and statistics.

    This page displays a split layout with:
    - A left sidebar containing the app logo, a date picker, and a donation link.
    - A right main container showing all scheduled games for the selected date,
      with interactive `GameCard` components and predicted outcomes.

    Users can select a different date using the date picker and update predictions
    by clicking the "Predict" button.

    Parameters
    ----------
    date : str
        The target date in `YYYY-MM-DD` format for which games, predictions,
        and statistics should be displayed.

    Returns
    -------
    None
        This function does not return a value. It renders a full-page UI
        using NiceGUI.

    Notes
    -----
    - Custom CSS is applied to remove default padding and borders and to style
      containers.
    - Game predictions and statistics are handled by the `GameList` class.
    - The date picker is bound to the `games_list.date` attribute to trigger
      updates when a new date is selected.
    - External data sources:
        - Game schedules and stats are sourced from preprocessed CSV files.
        - Data attribution: Basketball Reference.
    """

    # Add custom CSS to remove unwanted borders and padding
    ui.add_css(".nicegui-content { margin: 0; padding: 0; height: 100vh; }")
    ui.add_css(".w-1/3, .w-2/3 { border: none; box-shadow: none; }")

    # Main app logic
    with ui.element("div").classes("w-full h-full flex"):

        # Creating the 2 containers
        with ui.element("div").classes(
            "w-1/3 flex justify-center items-center fixed h-full"
        ).style("background-color: #333436;"):
            date_container: ui.element = ui.element("div")

        with ui.element("div").classes("w-2/3 ml-auto h-full overflow-auto p-16").style(
            "background-color: #5a5f70;"
        ):
            cards_container: ui.element = ui.element("div")

        # Rendering the games list
        with cards_container:
            games_list: GameList = GameList(date)
            with ui.column(align_items="center"):
                games_list.render()

        # Creating the date picker
        with date_container:
            with ui.column(align_items="center"):
                ui.image("static/logo.svg").classes("mb-2")
                with ui.link(target="https://www.buymeacoffee.com/saccofrancesco"):
                    ui.image(
                        "https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=saccofrancesco&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"
                    ).classes("w-[250px]")
                date_picker: ui.date = (
                    ui.date(date)
                    .bind_value_to(games_list, "date")
                    .style("border-radius: 16px; background-color: #e3e4e6;")
                    .props(
                        '''minimal color=orange-14 :options="date => {const d = new Date(date); const start = new Date('2025-10-20'); const end = new Date('2026-04-12'); return d >= start && d <= end;}"'''
                    )
                    .classes("mt-2")
                )

                ui.button(
                    "Predict", on_click=lambda: ui.navigate.to(f"/{date_picker.value}")
                ).props("rounded push size=lg color=orange-14").classes(
                    "rounded-2xl mt-4"
                )

                with ui.row().classes("mt-4 justify-center items-center gap-2"):
                    ui.label("Data provided by: ").style("color: #e3e4e6;")
                    ui.link(
                        "Basketaball Reference", "https://www.basketball-reference.com"
                    ).style("color: #e3e4e6;")


# Creating the Head-2-Head plot component
class H2HPlot:
    def __init__(
        self,
        stat: str,
        date: str,
        window: int,
        team1: str,
        team2: str,
        home_color: str,
        away_color: str,
        csv_path: str,
    ) -> None:
        """
        Component to render a head-to-head (H2H) performance plot between two teams.

        This class generates an interactive line chart comparing a specific
        statistical metric for two teams over their most recent games prior
        to a selected date. It uses historical game data from a CSV file
        and renders the chart with NiceGUI's `ui.highchart`.

        Parameters
        ----------
        stat : str
            The statistical metric to plot (must exist in the CSV columns).
        date : str
            Reference date in `YYYY-MM-DD` format. Only games before this
            date are included in the plot.
        team1 : str
            Name of the first team (home team).
        team2 : str
            Name of the second team (away team).
        home_color : str
            Hex color code for the first team's plot line.
        away_color : str
            Hex color code for the second team's plot line.
        csv_path : str
            Path to the CSV file containing historical team statistics.

        Notes
        -----
        - The plot displays up to the last 25 games for each team prior to the
          specified date.
        - The x-axis represents game dates, formatted as month/day.
        - The y-axis shows the selected statistic values.
        - Series colors are set according to `home_color` and `away_color`.
        - Raises ValueError if the specified stat is not present in the dataset.
        """

        # Storing vars for future plot updates
        self.stat: str = stat
        self.date: str = date
        self.window: int = window
        self.team1: str = team1
        self.team2: str = team2
        self.home_color: str = home_color
        self.away_color: str = away_color
        self.path: str = csv_path

        # Plotting at first component mount
        self.plot_stat()

    @ui.refreshable
    def plot_stat(self) -> ui.plotly:
        """
        Render or refresh the head-to-head plot.

        Loads the CSV data, filters games by date, generates series for
        each team, and configures a Highcharts line chart.

        Returns
        -------
        ui.plotly
            The NiceGUI Highcharts plot component for the H2H comparison.

        Raises
        ------
        ValueError
            If the selected stat is not found in the CSV dataset columns.
        """

        # Load data
        df: pd.DataFrame = pd.read_csv(self.path, parse_dates=["date"])

        # Checking if the selected stat is present in the column
        if self.stat not in df.columns:
            raise ValueError(f"'{self.stat}' not found in dataset columns.")

        # Specify the start date (converting to timestamp)
        start_date: pd.Timestamp = pd.to_datetime(self.date)

        # Function to convert date to JS timestamp (ms since epoch)
        def make_series(df: pd.DataFrame, team: str, color: str) -> dict[str, str]:

            # Filter for games starting from the given date and going backwards
            df_team: pd.DataFrame = (
                df[(df["team"] == team) & (df["date"] < start_date)]
                .sort_values("date", ascending=False)
                .head(self.window)
            )  # Get the N game (controlled by the window input)

            # Prepare the data
            data: list[str] = [
                [int(d.date.timestamp() * 1000), float(getattr(d, self.stat))]
                for d in df_team.itertuples()
            ]
            return {
                "name": team,
                "data": data,
                "color": color,
            }

        # Generate both series
        series: list[dict[str, str]] = [
            make_series(df, self.team1, self.home_color),
            make_series(df, self.team2, self.away_color),
        ]

        # Highcharts config with datetime x-axis
        config: dict[str, dict[str, str]] = {
            "chart": {
                "type": "line",
                "spacingTop": 25,
                "spacingBottom": 25,
            },
            "title": {
                "text": f"{self.team1} vs {self.team2} {stat_to_full_name_desc[self.stat]}"
            },
            "xAxis": {
                "type": "datetime",
                "labels": {"format": "{value:%b %d}"},
            },
            "yAxis": {"title": {"text": stat_to_full_name_desc[self.stat]}},
            "legend": {
                "layout": "horizontal",
                "align": "center",
                "verticalAlign": "top",
            },
            "tooltip": {
                "xDateFormat": "%b %d, %Y",
                "shared": True,
            },
            "series": series,
        }

        ui.highchart(options=config).classes("rounded-lg")


# Single game details page
@ui.page("/{date}/{game}")
def game(date: str, game: str) -> None:
    """
    Render a single game details page with team stats and head-to-head plot.

    This page displays a detailed view for a specific game, including:
    - Team logos, names, and win probabilities
    - Visual win probability bars
    - Interactive head-to-head (H2H) plot for selectable statistics
    - A dropdown to select different stats to visualize

    A back button allows users to return to the main date page.

    Parameters
    ----------
    date : str
        The date of the game in `YYYY-MM-DD` format.
    game : str
        JSON-encoded string representing the game object with home/away
        team names, statistics, and prediction probabilities.

    Returns
    -------
    None
        This function does not return a value. It renders the UI directly
        using NiceGUI.

    Notes
    -----
    - The `game` parameter is decoded using `json.loads` after URL unquoting.
    - Team colors are determined using `get_best_color_pair`.
    - H2H plots are created with the `H2HPlot` class, allowing interactive
      selection of statistics to display.
    - Custom CSS is applied to style the layout, align elements, and set
      background colors.
    """

    # Re-converting the game object
    game: list[dict[str, str | int | float]] = json.loads(unquote(game))

    # Add custom CSS to remove unwanted borders and padding
    ui.add_css(".nicegui-content { margin: 0; padding: 0; height: 100vh; }")
    ui.add_css(".nicegui-content { display: flex; flex-direction: column; }")

    # Alligning the details card to the center
    ui.add_css(".nicegui-content { justify-content: center;  align-items: center; }")

    # Customizing the bg color
    ui.add_css(".nicegui-content { background-color: #5a5f70; }")

    # Back button
    with ui.page_sticky("top-left", x_offset=32, y_offset=32).classes("mt-8 ml-8"):
        ui.icon("arrow_back").classes("cursor-pointer text-3xl").style(
            "color: #e3e4e6"
        ).on("click", lambda: ui.navigate.to(f"/{date}"))

    # Creating the card fot the games details
    card: ui.card = (
        ui.card()
        .classes("m-4 p-6 rounded-2xl shadow-md border w-[850px]")
        .style("background-color: #e3e4e6;")
    )

    # Filling the card
    with card:

        # Calculating the color for each team
        home_color, away_color = get_best_color_pair(
            game["home_team"], game["away_team"]
        )

        # Row for Team Logos and "VS"
        with ui.row(align_items="center").classes(
            "items-center justify-between w-full"
        ):
            ui.image(f"static/{game['home_team']}.png").classes("w-28")
            ui.image(f"static/vs.png").classes("w-12")
            ui.image(f"static/{game['away_team']}.png").classes("w-28")

        # Row for Team Names and Win Probabilities
        with ui.row(align_items="stretch").classes("justify-between w-full"):
            with ui.column(align_items="start"):
                ui.label(game["home_team"]).classes("text-left text-md font-bold")
                ui.label(f"W {game['home_prob']} %").classes(
                    f"text-left text-md font-bold"
                )
            with ui.column(align_items="end"):
                ui.label(game["away_team"]).classes("text-right text-md font-bold")
                ui.label(f"W {game['away_prob']} %").classes(
                    f"text-right text-md font-bold"
                )

        # HTML element to create W % bars
        with ui.element("div").classes("flex w-full h-6"):
            ui.element("div").style(
                f"flex: {game['home_prob']}; background-color: {home_color}"
            ).classes("rounded-md mr-1")
            ui.element("div").style(
                f"flex: {game['away_prob']}; background-color: {away_color}"
            ).classes("rounded-md ml-1")

        # Creating the 2 containers for the selection and plotting of a specified stat
        selectors_section: ui.element = ui.element("div").classes("w-full")
        plotting_section: ui.element = ui.element("div").classes("w-full")

        # Creating a first plot
        with plotting_section:
            plot: H2HPlot = H2HPlot(
                "pts",
                date,
                10,
                game["home_team"],
                game["away_team"],
                home_color,
                away_color,
                "./data/csv/averages.csv",
            )

        # Dropdown selectin to choose stats, and used game window, to display for both teams
        with selectors_section:
            with ui.grid(columns="1fr 1fr"):
                ui.select(
                    stat_to_full_name_desc,
                    label="Selected a stat:",
                    value="pts",
                    with_input=True,
                    on_change=plot.plot_stat.refresh,
                ).style("border-radius: 0.25rem;").classes("w-full").props(
                    "outlined color=grey-9  bg-color=grey-2"
                ).bind_value_to(
                    plot, "stat"
                )
                ui.select(
                    [n for n in range(5, 26)],
                    value=10,
                    label="Selected a game window:",
                    with_input=True,
                    on_change=plot.plot_stat.refresh,
                ).style("border-radius: 0.25rem;").classes("w-full").props(
                    "outlined color=grey-9  bg-color=grey-2"
                ).bind_value_to(
                    plot, "window"
                )


# Running the app
ui.run(title="Deepshot AI", favicon="static/icon.png")
