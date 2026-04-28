from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from app.services import nba_service

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/live", tags=["Live"])

@router.get("/games")
def live_games(request: Request):
  result = nba_service.get_live_games()
  return templates.TemplateResponse(
    "live.html",
    {
      "request": request,
      "games": result
    }
  )
