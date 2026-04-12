"""Adjust predictions based on goalie matchup."""
from dataclasses import dataclass
from typing import Optional

LEAGUE_AVG_SAVE_PCT = 0.905

@dataclass
class GoalieAdjustment:
    """Adjustment to opponent's expected goals."""
    goalie_name: str
    save_pct: float
    adjustment: float  # Negative = fewer goals expected
    confidence: str
    gsaa: Optional[float] = None       # Goals Saved Above Average (NHL metric)
    hd_save_pct: Optional[float] = None  # High-danger save percentage
    method: str = "sv_pct"             # "sv_pct" | "gsaa" | "hd_sv_pct" | "blended"


def calculate_goalie_adjustment(
    goalie_save_pct: float,
    sample_size: int
) -> GoalieAdjustment:
    """
    Calculate goal adjustment based on goalie vs league average.
    
    Each 1% above/below average SV% ≈ 0.3 goals difference
    """
    diff_from_avg = goalie_save_pct - LEAGUE_AVG_SAVE_PCT
    
    # Base adjustment: 30 shots/game * SV% difference
    base_adjustment = -diff_from_avg * 30
    
    # Reduce confidence for small sample sizes
    if sample_size < 10:
        confidence = "low"
        adjustment = base_adjustment * 0.5  # Regress heavily
    elif sample_size < 20:
        confidence = "medium"
        adjustment = base_adjustment * 0.75
    else:
        confidence = "high"
        adjustment = base_adjustment
    
    return GoalieAdjustment(
        goalie_name="",  # Fill in caller
        save_pct=goalie_save_pct,
        adjustment=round(adjustment, 2),
        confidence=confidence,
        method="sv_pct",
    )


def calculate_goalie_adjustment_with_analytics(
    goalie_name: str,
    save_pct: float,
    sample_size: int,
    gsaa: Optional[float] = None,
    hd_save_pct: Optional[float] = None,
    gsaa_weight: float = 0.50,
) -> GoalieAdjustment:
    """
    Calculate a richer goalie adjustment using Goals Saved Above Average (GSAA)
    and high-danger save percentage when available.

    Method:
        1. Legacy save-percentage adjustment (always computed).
        2. GSAA-per-game adjustment: directly measures how many extra/fewer
           goals this goalie saves vs average.  Sign already correct — positive
           GSAA means fewer goals allowed.
        3. High-danger SV% adjustment on top of the primary estimate.

    The function blends legacy and GSAA estimates weighted by ``gsaa_weight``
    when GSAA is available, otherwise falls back to the legacy method.

    Args:
        goalie_name: Display name for the goalie.
        save_pct: Season save percentage.
        sample_size: Games played (controls regression to mean).
        gsaa: Goals Saved Above Average season total (from NHL analytics API).
              Positive = goalie is better than average.
        hd_save_pct: High-danger save percentage.  League average ≈ 0.830.
        gsaa_weight: Blend weight on the GSAA-based estimate (0–1).

    Returns:
        GoalieAdjustment with the blended adjustment and metadata.
    """
    # ---- Legacy estimate ----
    legacy = calculate_goalie_adjustment(save_pct, sample_size)
    legacy.goalie_name = goalie_name

    if gsaa is None:
        legacy.hd_save_pct = hd_save_pct
        return legacy

    # ---- GSAA-based estimate ----
    # Convert season GSAA to a per-game adjustment.
    # GSAA > 0 → goalie saves more → opponent scores fewer → negative adjustment.
    gsaa_per_game = gsaa / max(sample_size, 1) if sample_size > 0 else 0.0
    gsaa_adjustment = -gsaa_per_game  # negative: opponent xG decreases

    # Regress GSAA estimate toward 0 for small samples
    if sample_size < 10:
        gsaa_adjustment *= 0.4
        confidence = "low"
    elif sample_size < 20:
        gsaa_adjustment *= 0.70
        confidence = "medium"
    else:
        confidence = "high"

    # ---- High-danger save pct adjustment (additive) ----
    hd_adj = 0.0
    LEAGUE_AVG_HD_SAVE_PCT = 0.830
    if hd_save_pct is not None:
        hd_diff = hd_save_pct - LEAGUE_AVG_HD_SAVE_PCT
        # ~5 HD shots per game; each 1% = 0.05 goals
        hd_adj = -(hd_diff * 5)
        # Cap so one metric doesn't dominate
        hd_adj = max(-0.5, min(0.5, hd_adj))

    # ---- Blend ----
    blended_adjustment = (
        (1 - gsaa_weight) * legacy.adjustment
        + gsaa_weight * gsaa_adjustment
        + hd_adj
    )

    return GoalieAdjustment(
        goalie_name=goalie_name,
        save_pct=save_pct,
        adjustment=round(blended_adjustment, 3),
        confidence=confidence,
        gsaa=gsaa,
        hd_save_pct=hd_save_pct,
        method="blended" if gsaa_weight > 0 else "sv_pct",
    )


def adjusted_xg_for_matchup(
    base_team_xg: float,
    opposing_goalie_sv_pct: float,
    opposing_goalie_games: int
) -> float:
    """
    Adjust a team's expected goals based on opposing goalie.
    
    Example:
        Team xG: 3.2
        Opposing goalie: 0.925 SV% (elite)
        Adjustment: -0.6 goals
        Adjusted xG: 2.6
    """
    adj = calculate_goalie_adjustment(opposing_goalie_sv_pct, opposing_goalie_games)
    return round(base_team_xg + adj.adjustment, 2)


def adjusted_xg_with_analytics(
    base_team_xg: float,
    opposing_goalie_sv_pct: float,
    opposing_goalie_games: int,
    opposing_goalie_name: str = "",
    opposing_goalie_gsaa: Optional[float] = None,
    opposing_goalie_hd_sv_pct: Optional[float] = None,
) -> float:
    """
    Adjust a team's expected goals using the enriched goalie model.

    Prefers GSAA + HD SV% when available, falls back to SV% only.
    """
    adj = calculate_goalie_adjustment_with_analytics(
        goalie_name=opposing_goalie_name,
        save_pct=opposing_goalie_sv_pct,
        sample_size=opposing_goalie_games,
        gsaa=opposing_goalie_gsaa,
        hd_save_pct=opposing_goalie_hd_sv_pct,
    )
    return round(max(0.5, base_team_xg + adj.adjustment), 2)
