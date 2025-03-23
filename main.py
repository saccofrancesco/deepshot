# Importing libraries
import requests
import bs4
import datetime
import csv
import pandas as pd
import joblib
import sklearn.ensemble

# Loading the model
model: sklearn.ensemble._forest.RandomForestClassifier = joblib.load(
    "./model/deepshot.pkl"
)
print(type(model))

# Get the next day NBA game
month: datetime.datetime = datetime.datetime.now().strftime("%B").lower()
year: datetime.datetime = datetime.datetime.now().strftime("%Y")
today: datetime.datetime = datetime.datetime.now().strftime(f"{year}-%m-%d")

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
            == today
        ):
            daily_game_rows.append(row)


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
for game in daily_game_rows:
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
