from nba_api.stats.endpoints import boxscoretraditionalv2
from datetime import datetime, timedelta
from app.utils.helper import convert_times, get_nba_game_date
from fastapi import HTTPException
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
from app.services.news_service import get_team_news

TEAM_MAP = {
  t["id"]: {
    "name": t["full_name"],
    "abbr": t["abbreviation"]
  }
  for t in teams.get_teams()
}

# Тоглолтын хуваарь
def schedule():
  date_str = get_nba_game_date()

  data = scoreboardv2.ScoreboardV2(game_date=date_str).get_dict()
  games = data['resultSets'][0]['rowSet']

  results = []
  for game in games:
    times = convert_times(game[0], game[4])
    results.append({
      "game_id": game[2],
      # 🏀 teams
      "home_team_id": game[6],
      "away_team_id": game[7],
      "matchup": game[5],
      "arena": game[15],
      "network": game[11],
      "time": times
    })
  return results

# Тоглолт дэлгэрэнгүй
def game_detail(game_id: str):
  try:
    box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    data = box.get_dict()

    home = data['resultSets'][0]['rowSet']
    away = data['resultSets'][1]['rowSet']
    
    # 🆚 H2H
    game = get_teams_by_gameid(game_id)
    home_abbr = game["home_team_name_short"]
    away_abbr = game["away_team_name_short"]
    h2h = get_h2h(home_abbr, away_abbr)

    # 🆕 NEWS ADD HERE
    news = get_team_news(
      home_abbr,
      away_abbr
    )

    return {
      "home": home if home else [],
      "away": away if away else [],
      "h2h_games": h2h,
      "status": "ok" if home and away else "not_started",
      "home_team": home_abbr,
      "away_team": away_abbr,
      "news": news,
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

def get_teams_by_gameid(game_id: str):
  try:
    # 🧠 loop over multiple days (fix core issue)
    today = datetime.now()

    for i in range(-2, 2):  # check ±2 days
      date = (today + timedelta(days=i)).strftime("%m/%d/%Y")

      sb = scoreboardv2.ScoreboardV2(game_date=date)
      games = sb.get_dict()['resultSets'][0]['rowSet']

      for g in games:
        if g[2] == game_id:
          return {
            "game_id": game_id,
            "home_team_id": g[6],
            "away_team_id": g[7],
            "home_team_name_short": TEAM_MAP[g[6]]["abbr"],
            "away_team_name_short": TEAM_MAP[g[7]]["abbr"],
            "matchup": g[5]
          }

    raise HTTPException(status_code=404, detail="Game not found")

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# =========================
# 🧠 CURRENT NBA SEASON ID
# =========================
def get_current_season_id():
  """
  Returns NBA season format like:
  2025-26 → "22025"
  """
  now = datetime.now()
  year = now.year

  # NBA season starts in October
  if now.month >= 10:
    return f"2{year}"
  else:
    return f"2{year - 1}"

# =========================
# 🗓 SEASON START DATE
# =========================
def get_season_start_date():
  """
  NBA season usually starts around October 1
  """
  now = datetime.now()
  year = now.year
  if now.month >= 10:
    return datetime(year, 10, 1)
  else:
    return datetime(year - 1, 10, 1)

# =========================
# ⚙️ FILTER: season start → today
# =========================
def filter_current_season_games(df):
  start_date = get_season_start_date()
  today = datetime.now()
  df["GAME_DATE_DT"] = df["GAME_DATE"].apply(
    lambda x: datetime.strptime(x, "%Y-%m-%d")
  )
  df = df[
    (df["GAME_DATE_DT"] >= start_date) &
    (df["GAME_DATE_DT"] <= today)
  ]
  return df

# =========================
# 🏀 MAIN H2H FUNCTION
# =========================
def get_h2h(team1, team2):
  gf = leaguegamefinder.LeagueGameFinder()
  df = gf.get_data_frames()[0]

  # 🗓 filter only current season range
  df = filter_current_season_games(df)

  # 🆚 H2H filter
  h2h = df[
    df["MATCHUP"].str.contains(team1) &
    df["MATCHUP"].str.contains(team2)
  ]

  # remove duplicates
  h2h = h2h.drop_duplicates(subset=["GAME_ID"])

  # sort newest first
  h2h = h2h.sort_values(by="GAME_DATE_DT", ascending=False)

  # 🏀 mark playoff games
  h2h["IS_PLAYOFF"] = h2h["SEASON_ID"].astype(str).str.startswith("4")

  return h2h[[
    "GAME_ID",
    "GAME_DATE",
    "MATCHUP",
    "WL",
    "PTS",
    "IS_PLAYOFF"
  ]].to_dict("records")

