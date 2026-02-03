"""NHL API client with caching and error handling."""
import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Any, Optional


class NHLClient:
    """Client for NHL API endpoints with caching."""
    
    BASE_WEB_API = "https://api-web.nhle.com/v1"
    BASE_STATS_API = "https://api.nhle.com/stats/rest/en"
    CACHE_DIR = Path("data_files/cache")
    
    def __init__(self, cache_ttl_minutes: int = 5):
        """
        Initialize NHL API client.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL."""
        # Create safe filename from URL
        safe_name = url.replace("https://", "").replace("/", "_").replace("?", "_").replace(":", "_")
        # Limit filename length
        safe_name = safe_name[-100:] if len(safe_name) > 100 else safe_name
        return self.CACHE_DIR / f"{safe_name}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached data is still fresh."""
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < self.cache_ttl
    
    def _fetch_sync(self, url: str) -> dict[str, Any]:
        """
        Synchronous fetch with caching.
        
        Args:
            url: Full URL to fetch
            
        Returns:
            JSON response as dictionary
        """
        cache_path = self._get_cache_path(url)
        
        # Return cached data if valid
        if self._is_cache_valid(cache_path):
            return json.loads(cache_path.read_text())
        
        # Fetch fresh data
        try:
            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            cache_path.write_text(json.dumps(data, indent=2))
            return data
            
        except httpx.TimeoutException:
            raise ConnectionError(f"Timeout fetching {url}")
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"HTTP {e.response.status_code} for {url}")
    
    # -------------------------------------------------------------------------
    # Schedule Endpoints
    # -------------------------------------------------------------------------
    
    def get_schedule(self, game_date: str) -> dict:
        """
        Get games for a specific date.
        
        Args:
            game_date: Date in YYYY-MM-DD format
            
        Returns:
            Schedule data with gameWeek array
        """
        url = f"{self.BASE_WEB_API}/schedule/{game_date}"
        return self._fetch_sync(url)
    
    def get_todays_games(self) -> list[dict]:
        """
        Get today's games with key betting info.
        
        Returns:
            List of game dictionaries
        """
        today = date.today().isoformat()
        schedule = self.get_schedule(today)
        
        games = []
        for game_week in schedule.get("gameWeek", []):
            for game in game_week.get("games", []):
                games.append({
                    "game_id": game["id"],
                    "start_time": game.get("startTimeUTC"),
                    "home_team": game["homeTeam"]["abbrev"],
                    "away_team": game["awayTeam"]["abbrev"],
                    "home_score": game["homeTeam"].get("score"),
                    "away_score": game["awayTeam"].get("score"),
                    "game_state": game.get("gameState"),
                    "venue": game.get("venue", {}).get("default", ""),
                    "game_type": game.get("gameType", 2),
                })
        return games
    
    # -------------------------------------------------------------------------
    # Standings Endpoints
    # -------------------------------------------------------------------------
    
    def get_standings(self) -> dict:
        """
        Get current league standings.
        
        Returns:
            Standings data with standings array
        """
        url = f"{self.BASE_WEB_API}/standings/now"
        return self._fetch_sync(url)
    
    # -------------------------------------------------------------------------
    # Team Endpoints
    # -------------------------------------------------------------------------
    
    def get_team_schedule(self, team: str, season: str = "20252026") -> dict:
        """
        Get all games for a team in a season.
        
        Args:
            team: Team abbreviation (e.g., "TOR")
            season: Season ID (e.g., "20252026")
            
        Returns:
            Team schedule data
        """
        url = f"{self.BASE_WEB_API}/club-schedule-season/{team}/{season}"
        return self._fetch_sync(url)
    
    def get_team_stats(self, season: str = "20252026") -> dict:
        """
        Get team statistics for a season.
        
        Args:
            season: Season ID
            
        Returns:
            Team stats data array
        """
        url = f"{self.BASE_STATS_API}/team/summary?cayenneExp=seasonId={season}"
        return self._fetch_sync(url)
    
    def get_team_summary(self, team_abbrev: str, season: str = "20252026") -> Optional[dict]:
        """
        Get stats for a specific team.
        
        Args:
            team_abbrev: Team abbreviation
            season: Season ID
            
        Returns:
            Team stats dictionary or None
        """
        stats = self.get_team_stats(season)
        
        for team in stats.get("data", []):
            if team.get("teamAbbrev") == team_abbrev:
                return {
                    "team": team_abbrev,
                    "games_played": team.get("gamesPlayed", 0),
                    "wins": team.get("wins", 0),
                    "losses": team.get("losses", 0),
                    "ot_losses": team.get("otLosses", 0),
                    "points": team.get("points", 0),
                    "goals_for": team.get("goalsFor", 0),
                    "goals_against": team.get("goalsAgainst", 0),
                    "goals_for_pg": team.get("goalsForPerGame", 0),
                    "goals_against_pg": team.get("goalsAgainstPerGame", 0),
                    "pp_pct": team.get("powerPlayPct", 0),
                    "pk_pct": team.get("penaltyKillPct", 0),
                    "shots_for_pg": team.get("shotsForPerGame", 0),
                    "shots_against_pg": team.get("shotsAgainstPerGame", 0),
                }
        return None
    
    # -------------------------------------------------------------------------
    # Player Endpoints
    # -------------------------------------------------------------------------
    
    def get_skater_stats(self, season: str = "20252026", limit: int = 100) -> list[dict]:
        """
        Get top skaters by points.
        
        Args:
            season: Season ID
            limit: Number of players to return
            
        Returns:
            List of skater stats
        """
        url = (
            f"{self.BASE_STATS_API}/skater/summary"
            f"?limit={limit}&cayenneExp=seasonId={season}"
            f"&sort=points&direction=DESC"
        )
        data = self._fetch_sync(url)
        
        return [
            {
                "player_id": p.get("playerId"),
                "name": p.get("skaterFullName"),
                "team": p.get("teamAbbrevs"),
                "position": p.get("positionCode"),
                "games": p.get("gamesPlayed", 0),
                "goals": p.get("goals", 0),
                "assists": p.get("assists", 0),
                "points": p.get("points", 0),
                "plus_minus": p.get("plusMinus", 0),
                "shots": p.get("shots", 0),
                "shooting_pct": p.get("shootingPct", 0),
                "toi_pg": p.get("timeOnIcePerGame", 0),
            }
            for p in data.get("data", [])
        ]
    
    def get_goalie_stats(self, season: str = "20252026", limit: int = 50) -> list[dict]:
        """
        Get goalie statistics.
        
        Args:
            season: Season ID
            limit: Number of goalies to return
            
        Returns:
            List of goalie stats
        """
        url = (
            f"{self.BASE_STATS_API}/goalie/summary"
            f"?limit={limit}&cayenneExp=seasonId={season}"
            f"&sort=wins&direction=DESC"
        )
        data = self._fetch_sync(url)
        
        return [
            {
                "player_id": g.get("playerId"),
                "name": g.get("goalieFullName"),
                "team": g.get("teamAbbrevs"),
                "games_played": g.get("gamesPlayed", 0),
                "games_started": g.get("gamesStarted", 0),
                "wins": g.get("wins", 0),
                "losses": g.get("losses", 0),
                "ot_losses": g.get("otLosses", 0),
                "save_pct": g.get("savePct", 0),
                "gaa": g.get("goalsAgainstAverage", 0),
                "shutouts": g.get("shutouts", 0),
                "saves": g.get("saves", 0),
                "shots_against": g.get("shotsAgainst", 0),
            }
            for g in data.get("data", [])
        ]
    
    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------
    
    def clear_cache(self, max_age_hours: int = 24) -> int:
        """
        Remove cache files older than specified hours.
        
        Args:
            max_age_hours: Maximum age of cache files to keep
            
        Returns:
            Number of files removed
        """
        if not self.CACHE_DIR.exists():
            return 0
        
        removed = 0
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        for cache_file in self.CACHE_DIR.glob("*.json"):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if mtime < cutoff:
                cache_file.unlink()
                removed += 1
        
        return removed
    
    def get_cache_size_mb(self) -> float:
        """Get total cache size in megabytes."""
        if not self.CACHE_DIR.exists():
            return 0.0
        
        total_bytes = sum(f.stat().st_size for f in self.CACHE_DIR.glob("*.json"))
        return round(total_bytes / (1024 * 1024), 2)
