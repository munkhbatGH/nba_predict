from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import live
from app.routers import players

app = FastAPI(
  title="NBA Stats API",
  version="1.0.0",
  description="A clean FastAPI service that fetches NBA player stats using nba_api."
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(live.router)
app.include_router(players.router)

@app.get("/", tags=["Root"])
def root():
  return {"message": "Welcome to the NBA Stats API!"}
