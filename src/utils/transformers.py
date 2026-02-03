"""Transform API responses to pandas DataFrames."""
import pandas as pd
from typing import Any


def schedule_to_df(schedule_data: dict) -> pd.DataFrame:
    """
    Convert schedule API response to DataFrame.
    
    Args:
        schedule_data: Raw response from /schedule/{date}
    
    Returns:
        DataFrame with game information
    """
    games = []
    
    for game_day in schedule_data.get("gameWeek", []):
        for game in game_day.get("games", []):
            games.append({
                "game_id": game["id"],
                "date": game_day.get("date"),
                "start_time": game.get("startTimeUTC"),
                "home_team": game["homeTeam"]["abbrev"],
                "away_team": game["awayTeam"]["abbrev"],
                "home_score": game.get("homeTeam", {}).get("score"),
                "away_score": game.get("awayTeam", {}).get("score"),
                "game_state": game.get("gameState"),
                "game_type": game.get("gameType"),
                "venue": game.get("venue", {}).get("default", ""),
            })
    
    return pd.DataFrame(games)


def standings_to_df(standings_data: dict) -> pd.DataFrame:
    """
    Convert standings API response to DataFrame.
    
    Args:
        standings_data: Raw response from /standings/now
    
    Returns:
        DataFrame with team standings
    """
    teams = []
    
    for team in standings_data.get("standings", []):
        teams.append({
            "team": team.get("teamAbbrev", {}).get("default"),
            "team_name": team.get("teamName", {}).get("default"),
            "division": team.get("divisionName"),
            "conference": team.get("conferenceName"),
            "games_played": team.get("gamesPlayed", 0),
            "wins": team.get("wins", 0),
            "losses": team.get("losses", 0),
            "ot_losses": team.get("otLosses", 0),
            "points": team.get("points", 0),
            "points_pct": team.get("pointPctg", 0),
            "goals_for": team.get("goalFor", 0),
            "goals_against": team.get("goalAgainst", 0),
            "goal_diff": team.get("goalDifferential", 0),
            "regulation_wins": team.get("regulationWins", 0),
            "home_wins": team.get("homeWins", 0),
            "home_losses": team.get("homeLosses", 0),
            "home_ot_losses": team.get("homeOtLosses", 0),
            "away_wins": team.get("roadWins", 0),
            "away_losses": team.get("roadLosses", 0),
            "away_ot_losses": team.get("roadOtLosses", 0),
            "streak": team.get("streakCode"),
            "l10_wins": team.get("l10Wins", 0),
            "l10_losses": team.get("l10Losses", 0),
            "l10_ot": team.get("l10OtLosses", 0),
        })
    
    return pd.DataFrame(teams)


def team_stats_to_df(stats_data: dict) -> pd.DataFrame:
    """
    Convert team stats API response to DataFrame.
    
    Args:
        stats_data: Raw response from /team/summary
    
    Returns:
        DataFrame with team statistics
    """
    teams = []
    
    for team in stats_data.get("data", []):
        teams.append({
            "team": team.get("teamAbbrev"),
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
            "faceoff_pct": team.get("faceoffWinPct", 0),
        })
    
    return pd.DataFrame(teams)


def goalies_to_df(goalie_data: list) -> pd.DataFrame:
    """
    Convert goalie stats list to DataFrame.
    
    Args:
        goalie_data: List of goalie dictionaries from API
    
    Returns:
        DataFrame with goalie statistics
    """
    return pd.DataFrame(goalie_data)


def skaters_to_df(skater_data: list) -> pd.DataFrame:
    """
    Convert skater stats list to DataFrame.
    
    Args:
        skater_data: List of skater dictionaries from API
    
    Returns:
        DataFrame with skater statistics
    """
    return pd.DataFrame(skater_data)
