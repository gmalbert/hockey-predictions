"""
scripts/export_best_bets.py — NHL (hockey-predictions)
Reads data_files/recommendations.json (Value Finder output) and writes
data_files/best_bets_today.json in the unified Sports Picks Grid schema.
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SPORT = "NHL"
MODEL_VERSION = "1.0.0"
SEASON = str(date.today().year)
OUT_PATH = Path("data_files/best_bets_today.json")
SRC_PATH = Path("data_files/recommendations.json")

BET_TYPE_MAP = {
    "ML": "Moneyline", "Moneyline": "Moneyline",
    "Puck Line": "Spread", "PL": "Spread",
    "Over": "Over/Under", "Under": "Over/Under", "Total": "Over/Under",
}


def _write(bets: list, notes: str = "") -> None:
    payload: dict = {
        "meta": {
            "sport": SPORT,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": MODEL_VERSION,
            "season": SEASON,
        },
        "bets": bets,
    }
    if notes:
        payload["meta"]["notes"] = notes
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"[{SPORT}] Wrote {len(bets)} bets -> {OUT_PATH}")


def _tier_from_edge(edge: float) -> str:
    if edge >= 0.08:
        return "Elite"
    elif edge >= 0.03:
        return "Strong"
    elif edge >= 0.01:
        return "Good"
    return "Standard"


def main() -> None:
    today = date.today()

    if not SRC_PATH.exists():
        _write([], f"Source file not found: {SRC_PATH}")
        return

    try:
        with open(SRC_PATH) as f:
            data = json.load(f)
    except Exception as e:
        _write([], f"Failed to parse {SRC_PATH}: {e}")
        return

    # recommendations.json may be a list or a dict with a "recommendations" key
    if isinstance(data, dict):
        recs = data.get("recommendations", data.get("bets", []))
    elif isinstance(data, list):
        recs = data
    else:
        _write([], "Unrecognised recommendations.json structure")
        return

    bets = []
    for rec in recs:
        game_date = str(rec.get("date", rec.get("game_date", ""))).split("T")[0]
        if game_date != str(today):
            continue

        edge_raw = rec.get("edge_percent", rec.get("edge", 0))
        try:
            edge = float(edge_raw) / 100 if float(edge_raw) > 1 else float(edge_raw)
        except (TypeError, ValueError):
            edge = 0.0

        if edge < 0.01:
            continue

        bet_type_raw = str(rec.get("bet_type", "ML"))
        bet_type = BET_TYPE_MAP.get(bet_type_raw, bet_type_raw)

        conf_raw = rec.get("model_prob", rec.get("confidence", rec.get("win_probability")))
        try:
            confidence = float(conf_raw)
        except (TypeError, ValueError):
            confidence = None

        home = str(rec.get("home_team", ""))
        away = str(rec.get("away_team", ""))
        game = rec.get("matchup", rec.get("game", f"{away} @ {home}"))

        bet: dict = {
            "game_date": game_date,
            "game_time": rec.get("game_time") or None,
            "game": game,
            "home_team": home,
            "away_team": away,
            "bet_type": bet_type,
            "pick": str(rec.get("recommendation", rec.get("pick", ""))),
            "confidence": confidence,
            "edge": edge,
            "tier": _tier_from_edge(edge),
            "odds": rec.get("odds") or None,
            "line": rec.get("line") or None,
            "notes": rec.get("notes") or None,
        }
        bets.append(bet)

    _write(bets, "" if bets else f"No NHL picks for {today}")


if __name__ == "__main__":
    main()
