from fastapi import APIRouter, HTTPException
from app.services import nba_service
from app.schemas.player_schema import PlayerResponse

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("/{player_name}", response_model=PlayerResponse)
def get_player(player_name: str):
  player = nba_service.get_player_by_name(player_name)
  if not player:
    raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")

  df = nba_service.get_player_career_stats(player["id"])
  result = nba_service.format_player_data(player, df)
  return result

@router.get("/live_scores")
def live_scores():
  result = nba_service.get_live_games()
  return result
