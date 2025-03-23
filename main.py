# Importing libraries
import requests
import bs4
import datetime

# Get the next day NBA game
month: datetime.datetime = datetime.datetime.now().strftime("%B").lower()
year: datetime.datetime = datetime.datetime.now().strftime("%Y")

# Composing the schedule URL
schedule_url: str = (
    f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
)

# Requesting and souping the schedule page
page: requests.models.Response = requests.get(schedule_url)
soup: bs4.BeautifulSoup = bs4.BeautifulSoup(page.content, "html.parser")

# Filtering the schedules
rows: list[bs4.element.Tag] = soup.find("tbody").find_all("tr")
