from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

class Batter(BaseModel):
    name: str
    runs: str
    balls: str
    strike_rate: str

class Bowler(BaseModel):
    name: str
    overs: str
    runs: str
    wickets: str

class InningScore(BaseModel):
    team: str
    score: str

class Innings(BaseModel):
    inning_score: List[InningScore] = []
    remarks: Optional[str] = None  # for post-table status

class MatchStatus(BaseModel):
    recent_balls: Optional[str] = None
    text: Optional[str] = None

class CricketMatch(BaseModel):
    post_title: str
    match_title: Optional[str] = None
    innings: List[Innings] = []
    current_batters: List[Batter] = []
    current_bowlers: List[Bowler] = []
    match_status: MatchStatus = MatchStatus()
    created_utc: Optional[int] = None
    url: Optional[str] = None
    reddit_id: Optional[str] = None
    subreddit: Optional[str] = None
    link_flair_text: Optional[str] = None

    # 🆕 Added fields
    cricinfo_url: Optional[str] = None
    match_id: Optional[str] = None

    @property
    def created_datetime(self) -> Optional[datetime]:
        """Convert created_utc to datetime object"""
        if self.created_utc:
            return datetime.fromtimestamp(self.created_utc, tz=timezone.utc)
        return None

    def is_from_today(self) -> bool:
        """Check if the match was created today"""
        if not self.created_datetime:
            return False

        today = datetime.now(timezone.utc).date()
        return self.created_datetime.date() == today

class MatchesResponse(BaseModel):
    count: int
    matches: List[CricketMatch]
    fetched_at: datetime

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    service: str = "cricket-parser-api"