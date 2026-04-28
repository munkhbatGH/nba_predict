from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from app.services import game_service

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/game", tags=["game"])

@router.get("/schedule")
def tomorrow_games(request: Request):
  result = game_service.schedule()
  return templates.TemplateResponse(
    "schedule.html",
    {
      "request": request,
      "games": result
    }
  )

@router.get("/{game_id}")
def game_detail(request: Request, game_id: str):
  result = game_service.game_detail(game_id)
  # print(f"result: {result}")
  return templates.TemplateResponse(
    "game.html",
    {
      "request": request,
      "home_players": result["home"],
      "away_players": result["away"],
      "h2h_games": result['h2h_games'],
      "status": result['status'],
      "home_team": result['home_team'],
      "away_team": result['away_team'],
      "news": result['news'],
    }
  )