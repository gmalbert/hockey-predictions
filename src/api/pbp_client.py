"""
Play-by-play data client using hockeyR-data GitHub repository.

Downloads pre-built seasonal PBP CSV files (2010-11 through 2023-24) and
exputes rolling team/goalie/player metrics for use in predictions.

Data source: https://github.com/danmorse314/hockeyR-data
Note: The hockeyR-data repo is updated to 2023-24. Use NHL API for current
      season shot-based data.
"""
from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# hockeyR-data base URL for raw CSV downloads
HOCKEYR_DATA_BASE = (
    "https://raw.githubusercontent.com/danmorse314/hockeyR-data/main/data"
)

# Columns we need from the full PBP (lite files have most of these)
REQUIRED_COLUMNS = [
    "event_type",
    "event_team_abbr",
    "home_abbreviation",
    "away_abbreviation",
    "game_date",
    "game_id",
    "strength_state",
    "xg",
    "event_player_1_name",
    "event_goalie_name",
    "period_type",
    "season_type",
]

# Fenwick events (unblocked shot attempts)
FENWICK_EVENTS = {"SHOT", "MISSED_SHOT", "GOAL"}

# All goal/shot events (Corsi)
CORSI_EVENTS = {"SHOT", "MISSED_SHOT", "GOAL", "BLOCKED_SHOT"}

CACHE_DIR = Path("data_files/historical")
PBP_CACHE_TTL_DAYS = 30  # Re-download season file at most once per month


def _season_to_filename(season_end_year: int) -> str:
    """
    Convert a season end year (e.g. 2024) to the hockeyR file name segment.

    2024 → "2023_24"
    """
    start = season_end_year - 1
    end_short = str(season_end_year)[-2:]
    return f"{start}_{end_short}"


def _cache_path(season_end_year: int) -> Path:
    """Return local cache path for a season's lite PBP parquet file."""
    return CACHE_DIR / "pbp" / f"pbp_{season_end_year}_lite.parquet"


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(days=PBP_CACHE_TTL_DAYS)


def download_season_pbp(season_end_year: int, timeout: float = 120.0) -> pd.DataFrame:
    """
    Download and cache the '_lite' play-by-play CSV for a given season.

    The lite files contain all key columns including ``xg``, shot distance,
    shot angle, event coordinates, event type, strength state, and player IDs.
    They omit shift-change events which cuts the file size roughly in half.

    Args:
        season_end_year: The year the season ended (e.g. 2024 for 2023-24).
        timeout: HTTP request timeout in seconds.

    Returns:
        DataFrame with play-by-play events.

    Raises:
        ConnectionError: If the download fails.
        ValueError: If season data is not available.
    """
    cache = _cache_path(season_end_year)
    if _is_cache_fresh(cache):
        logger.info("Loading PBP %d from cache: %s", season_end_year, cache)
        return pd.read_parquet(cache)

    seg = _season_to_filename(season_end_year)
    url = f"{HOCKEYR_DATA_BASE}/play_by_play_{seg}_lite.csv.gz"
    logger.info("Downloading hockeyR PBP: %s", url)

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Season {season_end_year} not available in hockeyR-data "
            f"(HTTP {exc.response.status_code}). "
            "The repo currently goes back to 2010-11 and up to 2023-24."
        ) from exc
    except httpx.RequestError as exc:
        raise ConnectionError(f"Network error downloading PBP data: {exc}") from exc

    df = pd.read_csv(
        io.BytesIO(resp.content),
        compression="gzip",
        low_memory=False,
    )

    # Keep only regular-season and playoff games; drop shootout periods
    if "season_type" in df.columns:
        df = df[df["season_type"] == "R"]
    if "period_type" in df.columns:
        df = df[df["period_type"] != "SO"]

    # Parse game_date to datetime
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    logger.info("Cached PBP %d → %s (%d rows)", season_end_year, cache, len(df))
    return df


# ---------------------------------------------------------------------------
# Team-level metrics
# ---------------------------------------------------------------------------

def compute_team_xg(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-team, per-game expected goals for and against.

    Only uses 5v5 strength-state events.

    Returns a DataFrame with columns:
        game_id, game_date, team, xgf, xga
    """
    shots = pbp[
        pbp["event_type"].isin(FENWICK_EVENTS)
        & pbp.get("strength_state", pd.Series(["5v5"] * len(pbp))).eq("5v5")
        & pbp["xg"].notna()
    ].copy()

    if shots.empty:
        return pd.DataFrame(columns=["game_id", "game_date", "team", "xgf", "xga"])

    records = []
    for (game_id, team), grp in shots.groupby(["game_id", "event_team_abbr"]):
        game_date = grp["game_date"].iloc[0] if "game_date" in grp.columns else None
        # In hockeyR data, the opponent is determined by home/away columns
        # For XGA: shots taken by the opponent against this team
        home = grp["home_abbreviation"].iloc[0]
        away = grp["away_abbreviation"].iloc[0]
        opponent = away if team == home else home

        xgf = grp["xg"].sum()
        records.append(
            {"game_id": game_id, "game_date": game_date, "team": team, "xgf": xgf}
        )

    df_for = pd.DataFrame(records)

    # Build XGA by aggregating opponent's shots
    df_against = shots.copy()
    df_against["defending_team"] = df_against.apply(
        lambda r: r["away_abbreviation"]
        if r["event_team_abbr"] == r["home_abbreviation"]
        else r["home_abbreviation"],
        axis=1,
    )
    df_against_agg = (
        df_against.groupby(["game_id", "defending_team"])["xg"]
        .sum()
        .reset_index()
        .rename(columns={"defending_team": "team", "xg": "xga"})
    )

    result = df_for.merge(df_against_agg, on=["game_id", "team"], how="outer")
    result = result.sort_values(["team", "game_date"]).reset_index(drop=True)
    return result


def compute_rolling_team_xg(
    pbp: pd.DataFrame,
    n_games: int = 10,
) -> dict[str, dict]:
    """
    Compute rolling N-game xGF/xGA per game and 5v5 Fenwick% for each team.

    Returns a dict keyed by team abbreviaton with keys:
        xgf_pg   – rolling avg xG for per game
        xga_pg   – rolling avg xG against per game
        xg_diff  – xgf_pg - xga_pg
        ff_pct   – Fenwick-for% at 5v5 (season to date)
        games    – number of games in the rolling window
    """
    if pbp.empty:
        return {}

    # --- xGF/xGA rolling ---
    game_xg = compute_team_xg(pbp)
    results: dict[str, dict] = {}

    for team, grp in game_xg.groupby("team"):
        recent = grp.sort_values("game_date").tail(n_games)
        n = len(recent)
        if n == 0:
            continue
        xgf_pg = recent["xgf"].sum() / n
        xga_pg = (
            recent["xga"].sum() / n if "xga" in recent.columns else float("nan")
        )
        results[team] = {
            "xgf_pg": round(xgf_pg, 3),
            "xga_pg": round(xga_pg, 3),
            "xg_diff": round(xgf_pg - xga_pg, 3),
            "games": n,
        }

    # --- 5v5 Fenwick% (season to date) ---
    fenwick = pbp[
        pbp["event_type"].isin(FENWICK_EVENTS)
        & pbp.get("strength_state", pd.Series(["5v5"] * len(pbp))).eq("5v5")
    ]
    ff_for = fenwick.groupby("event_team_abbr").size()
    # Total fenwick attempts per game is split between the two teams
    all_teams = set(pbp["home_abbreviation"].unique()) | set(
        pbp["away_abbreviation"].unique()
    )
    for team in all_teams:
        ff = ff_for.get(team, 0)
        # Total fenwick events involving this team (for + against)
        team_games = pbp[
            (pbp["home_abbreviation"] == team) | (pbp["away_abbreviation"] == team)
        ]
        total_fenwick = len(
            team_games[team_games["event_type"].isin(FENWICK_EVENTS)]
        )
        ff_pct = ff / total_fenwick if total_fenwick > 0 else 0.5
        if team in results:
            results[team]["ff_pct"] = round(ff_pct, 4)
        else:
            results[team] = {"ff_pct": round(ff_pct, 4), "games": 0}

    return results


# ---------------------------------------------------------------------------
# Goalie metrics
# ---------------------------------------------------------------------------

def compute_goalie_gsax(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Goals Saved Above Expected (GSAX) per goalie.

    GSAX = sum(xg_against) - actual_goals_against

    Positive GSAX means the goalie saved more than expected — they are
    performing above the model's expectation.

    Returns a DataFrame with columns:
        goalie, team, xg_against, goals_against, gsax, shots_faced, games
    """
    # Shots on goal are SHOT and GOAL events (not MISSED or BLOCKED)
    shot_events = pbp[
        pbp["event_type"].isin({"SHOT", "GOAL"}) & pbp["xg"].notna()
    ]

    if "event_goalie_name" not in shot_events.columns:
        return pd.DataFrame()

    shot_events = shot_events[shot_events["event_goalie_name"].notna()]

    # Determine defending team (opponent of shooter)
    def defending_team(row):
        if row["event_team_abbr"] == row.get("home_abbreviation", ""):
            return row.get("away_abbreviation", "")
        return row.get("home_abbreviation", "")

    shot_events = shot_events.copy()
    shot_events["defending_team"] = shot_events.apply(defending_team, axis=1)

    agg = (
        shot_events.groupby(["event_goalie_name", "defending_team"])
        .agg(
            xg_against=("xg", "sum"),
            goals_against=("event_type", lambda x: (x == "GOAL").sum()),
            shots_faced=("event_type", "count"),
        )
        .reset_index()
        .rename(
            columns={
                "event_goalie_name": "goalie",
                "defending_team": "team",
            }
        )
    )

    # Count games per goalie (approximated by unique game_id)
    games_agg = (
        shot_events.groupby("event_goalie_name")["game_id"]
        .nunique()
        .reset_index()
        .rename(columns={"event_goalie_name": "goalie", "game_id": "games"})
    )
    agg = agg.merge(games_agg, on="goalie", how="left")
    agg["gsax"] = round(agg["xg_against"] - agg["goals_against"], 3)
    agg["gsax_per_game"] = round(
        agg["gsax"] / agg["games"].clip(lower=1), 3
    )
    return agg.sort_values("gsax", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Skater metrics
# ---------------------------------------------------------------------------

def compute_player_gax(pbp: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Goals Above Expected (GAX) per skater.

    GAX = actual_goals - sum(xg_for_shooter)

    Positive: player scores more than their shots predict → hot hand / elite
    Negative: player under-scores relative to shot quality → regression risk

    Returns a DataFrame with columns:
        player, team, goals, xg, gax, shots, gax_per_60
    """
    shots = pbp[
        pbp["event_type"].isin(FENWICK_EVENTS)
        & pbp["xg"].notna()
        & pbp.get("event_player_1_name", pd.Series([None] * len(pbp))).notna()
    ].copy()

    if shots.empty or "event_player_1_name" not in shots.columns:
        return pd.DataFrame()

    agg = (
        shots.groupby(["event_player_1_name", "event_team_abbr"])
        .agg(
            goals=("event_type", lambda x: (x == "GOAL").sum()),
            xg=("xg", "sum"),
            shots=("event_type", "count"),
        )
        .reset_index()
        .rename(
            columns={"event_player_1_name": "player", "event_team_abbr": "team"}
        )
    )

    agg["gax"] = round(agg["goals"] - agg["xg"], 3)
    agg["shooting_pct"] = round(agg["goals"] / agg["shots"].clip(lower=1) * 100, 2)
    agg["xg_shooting_pct"] = round(agg["xg"] / agg["shots"].clip(lower=1) * 100, 2)
    return agg.sort_values("gax", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Convenience loader (auto-picks most recent available season)
# ---------------------------------------------------------------------------

def load_most_recent_season(max_year: int = 2024) -> Optional[pd.DataFrame]:
    """
    Try to load or download the most recent available hockeyR season.

    The repo currently contains data through 2023-24 (end year = 2024).

    Args:
        max_year: Latest season end year to attempt (default 2024).

    Returns:
        PBP DataFrame or None if unavailable.
    """
    for year in range(max_year, 2009, -1):
        cache = _cache_path(year)
        if _is_cache_fresh(cache):
            return pd.read_parquet(cache)
        try:
            return download_season_pbp(year)
        except (ValueError, ConnectionError) as exc:
            logger.debug("Season %d unavailable: %s", year, exc)
            continue
    return None


def get_cached_metrics(season_end_year: int = 2024) -> dict:
    """
    Load pre-computed rolling metrics from the local metrics cache.

    Computes them if the cache doesn't exist or is stale.
    Returns a dict with keys: 'teams', 'goalies', 'players', 'computed_at'.
    """
    metrics_path = CACHE_DIR / "pbp" / f"metrics_{season_end_year}.json"

    if metrics_path.exists():
        age = datetime.now() - datetime.fromtimestamp(metrics_path.stat().st_mtime)
        if age < timedelta(days=PBP_CACHE_TTL_DAYS):
            with open(metrics_path) as f:
                return json.load(f)

    pbp = load_most_recent_season(max_year=season_end_year)
    if pbp is None:
        return {}

    team_metrics = compute_rolling_team_xg(pbp, n_games=10)
    goalie_metrics = compute_goalie_gsax(pbp)
    player_metrics = compute_player_gax(pbp)

    result = {
        "teams": team_metrics,
        "goalies": goalie_metrics.to_dict(orient="records") if not goalie_metrics.empty else [],
        "players": player_metrics.to_dict(orient="records") if not player_metrics.empty else [],
        "computed_at": datetime.now().isoformat(),
        "season_end_year": season_end_year,
    }

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(result, f, default=str)

    return result
