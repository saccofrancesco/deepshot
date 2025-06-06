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

# Adding static files (teams' logos)
app.add_static_files("./static", "static")

# Global dictionary to hold team stats
team_stats_data: defaultdict = defaultdict(list)
headers: list[str] = list()


# Load CSV once
def load_team_stats(file_path: str = "./data/csv/averages.csv"):
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
    "nrtg": "Net Rating (NRtg)",
    "ast_tov": "Assist-to-Turnover (AST/TOV)",
    "ast_ratio": "Assist Ratio (ASTr)",
}

# Stats -> Tooltip (for advanced one)
stats_to_tooltip: dict[str, str] = {
    "ortg": "An estimate of points scored per 100 possessions",
    "drtg": "An estimate of points allowed per 100 possesions",
    "pace": "An estimate of possessions per 48 minutes",
    "ftr": "Number of FT Attempts Per FG Attempt",
    "3ptar": "Percentage of FG Attempts from 3-Point Range",
    "ts": "A measure of shooting efficiency that takes into account 2-point field goals, 3-point field goals, and free throws",
    "trb_pct": "An estimate of the percentage of available rebounds grabbed",
    "ast_pct": "An estimate of the percentage of teammate field goals assisted",
    "stl_pct": "An estimate of the percentage of opponent possesions that end with a steal",
    "blk_pct": "An estimate of the percentage of opponent two-point field goal attempt blocked",
    "efg_pct": "This statistics adjusts for the fact that a 3-point field goal is worth one more point than a 2-point field goal",
    "tov_pct": "An estimate of turnovers commited per 100 plays",
    "orb_pct": "An estimate of the percentage of available offensive rebounds grabbed",
    "nrtg": "Measures the overall efficiency of a team in both scoring and preventing points",
    "ast_tov": "The ratio of assists to turnovers, measuring the team's passing efficiency",
    "ast_ratio": "The percentage of a team’s possessions that end in an assist",
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
    "Utah Jazz": ["#f9a01b"],
    "Washington Wizards": ["#002b5c", "#e31837"],
}


# Function to get the best colors from a set of two list mapped by two team names
def get_best_color_pair(team1: str, team2: str) -> tuple[str, str]:

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

    games: list = list()

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
    if team_name not in team_stats_data:
        return (None, None)

    for date_str, row in team_stats_data[team_name]:
        if date_str < target_date:
            return (headers[2:], row[2:])  # Skip date and team name

    return (None, None)


# Creating the Card UI
class GameCard(ui.card):
    def __init__(self, game: dict[str, str | int | float], date: str) -> None:

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
    def render(self) -> None:

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
                GameCard(game, self.date)
        except:
            pass


# Redirect to page
@ui.page("/")
def redirect() -> None:
    ui.navigate.to(f"/2025-04-13")


# Home day prediction and stats page template
@ui.page("/{date}")
def home(date: str) -> None:

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
                        "https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
                    ).classes("w-[250px]")
                date_picker: ui.date = (
                    ui.date(date)
                    .bind_value_to(games_list, "date")
                    .style("border-radius: 16px; background-color: #e3e4e6;")
                    .props(
                        '''minimal color=orange-14 :options="date => {const d = new Date(date); const start = new Date('2024-10-21'); const end = new Date('2025-04-13'); return d >= start && d <= end;}"'''
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
        team1: str,
        team2: str,
        home_color: str,
        away_color: str,
        csv_path: str,
    ) -> None:

        # Storing vars for future plot updates
        self.stat: str = stat
        self.date: str = date
        self.team1: str = team1
        self.team2: str = team2
        self.home_color: str = home_color
        self.away_color: str = away_color
        self.path: str = csv_path

        # Plotting at first component mount
        self.plot_stat()

    @ui.refreshable
    def plot_stat(self) -> ui.plotly:

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
                .head(25)
            )  # Get the last 25 games

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
                game["home_team"],
                game["away_team"],
                home_color,
                away_color,
                "./data/csv/averages.csv",
            )

        # Dropdown selectin to choose stats to display for both teams
        with selectors_section:
            ui.select(
                stat_to_full_name_desc,
                value="pts",
                with_input=True,
                on_change=plot.plot_stat.refresh,
            ).style("border-radius: 0.25rem;").classes("w-full").props(
                "outlined color=grey-9  bg-color=grey-2"
            ).bind_value_to(
                plot, "stat"
            )


# Running the app
ui.run(title="Deepshot AI", favicon="static/icon.png")
