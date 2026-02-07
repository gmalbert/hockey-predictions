"""Calculate betting impact of injuries."""
from typing import Dict, List
from dataclasses import dataclass

# Base impact values (goals per game)
POSITION_IMPACTS = {
    "G": {  # Goalies
        "critical": 0.50,  # Starter out
        "high": 0.00,      # Backup out (no impact if starter plays)
    },
    "C": {  # Centers
        "critical": 0.35,  # 1C
        "high": 0.20,      # 2C
        "medium": 0.10,    # 3C
        "low": 0.03        # 4C
    },
    "W": {  # Wingers
        "critical": 0.30,  # Top-line winger
        "high": 0.18,
        "medium": 0.08,
        "low": 0.03
    },
    "D": {  # Defensemen
        "critical": 0.25,  # #1 D
        "high": 0.15,
        "medium": 0.08,
        "low": 0.03
    }
}

@dataclass
class InjuryImpact:
    """Impact assessment for a team's injuries."""
    team: str
    offensive_impact: float  # Expected goals for reduction
    defensive_impact: float  # Expected goals against increase
    net_impact: float
    key_injuries: List[str]

def calculate_injury_impact(injuries: List[dict]) -> InjuryImpact:
    """
    Calculate total impact of injuries on team performance.
    
    Returns expected goal differential change.
    """
    offensive_impact = 0.0
    defensive_impact = 0.0
    key_injuries = []
    
    for injury in injuries:
        if injury.get("status") in ["healthy", "probable"]:
            continue  # Likely playing
        
        position = injury.get("position", "W")[0]  # First letter
        tier = injury.get("player_tier", "medium")
        
        impact = POSITION_IMPACTS.get(position, {}).get(tier, 0.05)
        
        if position in ["C", "W"]:
            offensive_impact += impact
        elif position == "D":
            # Defensemen affect both
            offensive_impact += impact * 0.3
            defensive_impact += impact * 0.7
        elif position == "G":
            defensive_impact += impact
        
        if tier in ["critical", "high"]:
            key_injuries.append(injury.get("player_name", "Unknown"))
    
    return InjuryImpact(
        team=injuries[0].get("team", "") if injuries else "",
        offensive_impact=round(offensive_impact, 2),
        defensive_impact=round(defensive_impact, 2),
        net_impact=round(-(offensive_impact + defensive_impact), 2),
        key_injuries=key_injuries
    )

def adjust_xg_for_injuries(
    base_xg: float,
    team_injuries: InjuryImpact,
    opponent_injuries: InjuryImpact
) -> float:
    """
    Adjust expected goals for injury situations.
    
    Team loses production from their injuries.
    Team gains production from opponent's defensive injuries.
    """
    # Reduce for own injuries
    adjusted = base_xg - team_injuries.offensive_impact
    
    # Boost for opponent's defensiveinjuries
    adjusted += opponent_injuries.defensive_impact
    
    return max(0.5, round(adjusted, 2))  # Floor at 0.5 xG
