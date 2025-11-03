from pydantic import BaseModel
from typing import List, Optional

class PlayerSummary(BaseModel):
    seasons_played: int
    total_points: int
    total_rebounds: int
    total_assists: int

class SeasonStats(BaseModel):
    season: str
    team: str
    games: int
    points: float
    rebounds: float
    assists: float

class PlayerResponse(BaseModel):
    player: str
    summary: PlayerSummary
    career_stats: List[SeasonStats]