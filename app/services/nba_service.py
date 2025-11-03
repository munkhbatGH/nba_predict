import datetime
from http.client import HTTPException
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard

def get_player_by_name(name: str):
  all_players = players.get_players()
  return next((p for p in all_players if p["full_name"].lower() == name.lower()), None)

def get_player_career_stats(player_id: int):
  career = playercareerstats.PlayerCareerStats(player_id=player_id)
  df = career.get_data_frames()[0]
  return df

def format_player_data(player, df: pd.DataFrame):
  summary = {
    "seasons_played": len(df),
    "total_points": int(df["PTS"].sum()),
    "total_rebounds": int(df["REB"].sum()),
    "total_assists": int(df["AST"].sum()),
  }

  stats = df[["SEASON_ID", "TEAM_ABBREVIATION", "GP", "PTS", "REB", "AST"]] \
    .rename(columns={
      "SEASON_ID": "season",
      "TEAM_ABBREVIATION": "team",
      "GP": "games",
      "PTS": "points",
      "REB": "rebounds",
      "AST": "assists"
    }) \
    .to_dict(orient="records")

  return {
    "player": player["full_name"],
    "summary": summary,
    "career_stats": stats
  }

def get_live_games():
  try:
    games = scoreboard.ScoreBoard()
    data = games.get_dict()
    results = []
    for game in data['scoreboard']['games']:
      results.append({
        "game_id": game['gameId'],
        "home_team": game['homeTeam']['teamName'],
        "away_team": game['awayTeam']['teamName'],
        "home_score": game['homeTeam']['score'],
        "away_score": game['awayTeam']['score'],
        "status": game['gameStatusText']
      })
    return results
  except KeyError as e:
    # Unexpected data structure from API
    raise HTTPException(status_code=502, detail=f"Unexpected API response: missing key {e}")
  except Exception as e:
    # Catch-all for any other errors
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
