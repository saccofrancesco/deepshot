# Importing libraries
import requests
import bs4
from collections import defaultdict
from rich.console import Console
from rich.progress import Progress
import sqlite3
import plotly.graph_objects as go
import plotly.io as pio

# Setting the browser to be the default renderer for charts
pio.renderers.default = "browser"

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
    "Phoenix Suns": "PH0",
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
        advanced_page: requests.models.Response = requests.get(advanced_url)
        progress.advance(task)

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
                    "ts": float(log.find("td", {"data-stat": "ts_pct"}).text),
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
                avg_value: float = (
                    sum(stats[d]["stats"][stat_key] for d in past_games)
                    / len(past_games)
                    if past_games
                    else stats[date]["stats"][stat_key]
                )
                stats[date]["average_stats"][stat_key] = round(avg_value, 2)
            progress.advance(task)

    console.print(
        f"[bold green]Data fetching complete for {team} - {season}![/bold green]"
    )
    return stats


# Plot agraph with both the day-to-day game metric and the average given a single stat
def plot_metric(stats, metric):

    # Extract the dates, stat values, and average values
    dates: list[str] = sorted(stats.keys())
    stat_values: list[int | float] = [stats[date]["stats"][metric] for date in dates]
    avg_values: list[int | float] = [
        stats[date]["average_stats"][metric] for date in dates
    ]

    # Create the Plotly figure
    fig: go.Figure = go.Figure()

    # Add the actual game-day stats trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=stat_values,
            mode="lines+markers",  # Show both lines and markers
            name=f"Game-day {metric}",
            marker=dict(
                size=10,
                color="#3C6E71",
                symbol="circle",
                line=dict(width=1, color="white"),
            ),
            line=dict(color="#3C6E71", width=2, smoothing=True),
        )
    )

    # Add the rolling average stats trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=avg_values,
            mode="lines+markers",  # Show both lines and markers
            name=f"Rolling Average {metric}",
            marker=dict(
                size=10,
                color="#F0A500",
                symbol="circle",
                line=dict(width=1, color="white"),
            ),
            line=dict(color="#F0A500", width=2, dash="dot", smoothing=True),
        )
    )

    # Update the layout to make the plot look modern and sleek
    fig.update_layout(
        title=f"{metric.capitalize()} - Game-day vs Rolling Average",
        xaxis_title="Game Dates",
        yaxis_title=metric.capitalize(),
        xaxis=dict(
            tickangle=-45,
            tickmode="array",
            tickvals=dates[::5],
            showgrid=False,
        ),
        yaxis=dict(showgrid=False),
        margin=dict(l=50, r=50, t=80, b=40),
        hovermode="x unified",
        template="plotly_dark",  # Dark theme for sleekness
        plot_bgcolor="#2A2A2A",  # Subtle dark background
        paper_bgcolor="#2A2A2A",  # Subtle dark background
        font=dict(family="Arial", color="white", size=14),  # Modern font styling
        legend=dict(
            title="Legend",
            font=dict(size=12),
            orientation="h",  # Horizontal legend for a clean look
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        title_font=dict(size=22, family="Arial, sans-serif"),
        hoverlabel=dict(bgcolor="rgba(0,0,0,0.7)", font_size=13, font_family="Arial"),
    )

    # Show the figure
    fig.show()


# Main
if __name__ == "__main__":
    team: str = "Golden State Warriors"
    year: str = "2015"
    stats = fetch_team_season_log(team, year)
