from fastapi import APIRouter, HTTPException
from app.services import nba_service

router = APIRouter(prefix="/live", tags=["Live"])

@router.get("/games")
def live_games():
  result = nba_service.get_live_games()
  return result
