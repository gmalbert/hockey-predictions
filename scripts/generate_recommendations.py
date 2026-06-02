"""
scripts/generate_recommendations.py — NHL (hockey-predictions)

Generates data_files/recommendations.json by:
  1. Fetching today's NHL schedule (and next few days)
  2. Loading team stats and analytics
  3. Running the xG / win-probability model
  4. Comparing to ESPN DraftKings odds
  5. Writing picks with positive edge

Reads by: scripts/export_best_bets.py (which then writes best_bets_today.json)
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add repo root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.api.nhl_client import NHLClient
from src.models.expected_goals import (
    TeamMetrics,
    calculate_expected_goals,
    calculate_expected_goals_with_analytics,
)
from src.models.win_probability import calculate_win_probability

OUT_PATH = ROOT / "data_files" / "recommendations.json"
MIN_EDGE = 0.03           # only include picks with ≥3 % edge
LOOKAHEAD_DAYS = 7


def _american_to_prob(odds: int | None) -> float | None:
    """American moneyline → implied probability (no vig removal)."""
    if odds is None:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return abs(odds) / (abs(odds) + 100.0)


def _tier(edge: float) -> str:
    if edge >= 0.08:
        return "Elite"
    elif edge >= 0.03:
        return "Strong"
    elif edge >= 0.01:
        return "Good"
    return "Standard"


def main() -> None:
    today = date.today()
    client = NHLClient(cache_ttl_minutes=60)

    # ── 1. Fetch upcoming games with odds ────────────────────────────────────
    print("[generate_recommendations] Fetching upcoming games with odds...")
    try:
        odds_games = client.get_espn_odds(days_ahead=LOOKAHEAD_DAYS)
    except Exception as e:
        print(f"[generate_recommendations] ESPN odds fetch failed: {e}")
        odds_games = []

    if not odds_games:
        print("[generate_recommendations] No upcoming games found — writing empty output")
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps([], indent=2))
        return

    # ── 2. Load team analytics (best effort) ────────────────────────────────
    print("[generate_recommendations] Loading team analytics...")
    try:
        analytics_data = client.get_team_analytics(season="20252026")
    except Exception as e:
        print(f"[generate_recommendations] Analytics fetch failed: {e} — using legacy model")
        analytics_data = {}

    # ── 3. Build recommendations ─────────────────────────────────────────────
    recommendations = []

    for game in odds_games:
        home_abbr = game.get("home_team")
        away_abbr = game.get("away_team")
        game_date_str = (game.get("date") or "")[:10]  # ISO date portion

        if not home_abbr or not away_abbr:
            continue

        # Parse DraftKings odds (prefer DK, fall back to first provider)
        dk_odds = None
        for provider in game.get("odds", []):
            if provider.get("provider") in ("DraftKings", "DraftKings Sportsbook"):
                dk_odds = provider
                break
        if dk_odds is None and game.get("odds"):
            dk_odds = game["odds"][0]

        home_ml = dk_odds.get("moneyline", {}).get("home") if dk_odds else None
        away_ml = dk_odds.get("moneyline", {}).get("away") if dk_odds else None

        home_implied = _american_to_prob(home_ml)
        away_implied = _american_to_prob(away_ml)

        # ── 4. Team stats for xG model ────────────────────────────────────
        try:
            home_stats = client.get_team_summary(home_abbr) or {}
            away_stats = client.get_team_summary(away_abbr) or {}
        except Exception:
            home_stats = away_stats = {}

        if not home_stats or not away_stats:
            print(f"[generate_recommendations] No stats for {away_abbr} @ {home_abbr} — skipping")
            continue

        try:
            home_tm = TeamMetrics.from_api_response(home_stats)
            away_tm = TeamMetrics.from_api_response(away_stats)
        except Exception as e:
            print(f"[generate_recommendations] TeamMetrics error for {away_abbr} @ {home_abbr}: {e}")
            continue

        home_analytics = analytics_data.get(home_abbr)
        away_analytics = analytics_data.get(away_abbr)

        if home_analytics and away_analytics:
            try:
                home_xg, away_xg = calculate_expected_goals_with_analytics(
                    home_tm, away_tm,
                    home_analytics=home_analytics,
                    away_analytics=away_analytics,
                    analytics_weight=0.5,
                )
                model_source = "Analytics blend"
            except Exception:
                home_xg, away_xg = calculate_expected_goals(home_tm, away_tm)
                model_source = "Legacy"
        else:
            home_xg, away_xg = calculate_expected_goals(home_tm, away_tm)
            model_source = "Legacy"

        try:
            probs = calculate_win_probability(home_xg, away_xg)
        except Exception as e:
            print(f"[generate_recommendations] Win prob error for {away_abbr} @ {home_abbr}: {e}")
            continue

        home_win_prob = probs.home_win
        away_win_prob = probs.away_win

        # Game time (human-readable)
        raw_dt = game.get("date", "")
        try:
            game_dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
            game_time = game_dt.astimezone().strftime("%-I:%M %p ET")
        except Exception:
            game_time = ""

        matchup = f"{away_abbr} @ {home_abbr}"
        game_date = game_date_str or today.isoformat()

        # ── 5. Edge calculation ───────────────────────────────────────────
        if home_implied is not None:
            home_edge = home_win_prob - home_implied
            if home_edge >= MIN_EDGE:
                recommendations.append({
                    "date":           game_date,
                    "game_time":      game_time,
                    "matchup":        matchup,
                    "home_team":      home_abbr,
                    "away_team":      away_abbr,
                    "bet_type":       "ML",
                    "recommendation": home_abbr,
                    "model_prob":     round(home_win_prob, 4),
                    "edge":           round(home_edge, 4),
                    "odds":           home_ml,
                    "notes":          model_source,
                })

        if away_implied is not None:
            away_edge = away_win_prob - away_implied
            if away_edge >= MIN_EDGE:
                recommendations.append({
                    "date":           game_date,
                    "game_time":      game_time,
                    "matchup":        matchup,
                    "home_team":      home_abbr,
                    "away_team":      away_abbr,
                    "bet_type":       "ML",
                    "recommendation": away_abbr,
                    "model_prob":     round(away_win_prob, 4),
                    "edge":           round(away_edge, 4),
                    "odds":           away_ml,
                    "notes":          model_source,
                })

    # ── 6. Write output ───────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(recommendations, indent=2, ensure_ascii=False))
    print(f"[generate_recommendations] Wrote {len(recommendations)} recommendations → {OUT_PATH}")


if __name__ == "__main__":
    main()
