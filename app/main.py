from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

from fastapi.staticfiles import StaticFiles

from app.routers import live
from app.routers import players
from app.routers import game

app = FastAPI(
  title="NBA Stats API",
  version="1.0.0",
  description="A clean FastAPI service that fetches NBA player stats using nba_api."
)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(live.router)
app.include_router(players.router)
app.include_router(game.router)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
  routes = []
  print(app.routes)
  for route in app.routes:
    path = route.path
    if path.startswith("/live") or path.startswith("/players") or path.startswith("/game"):
      routes.append({ "path": route.path, "name": route.name })

  print(routes)
  return templates.TemplateResponse(
    "index.html",
    {
      "request": request,
      "title": "NBA Stats API",
      "message": "Welcome to your dashboard 🚀",
      "routes": routes,
    }
  )

# @app.get("/live-ui", response_class=HTMLResponse)
# async def live_ui(request: Request):
#   # call your own API internally
#   async with httpx.AsyncClient() as client:
#     res = await client.get("http://localhost:8000/live/games")
#     games = res.json()
#   return templates.TemplateResponse(
#     "live.html",
#     {
#       "request": request,
#       "games": games
#     }
#   )
