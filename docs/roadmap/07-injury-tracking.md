# Injury Tracking Roadmap

## Overview
Injuries significantly impact NHL betting outcomes. Missing key players affects team performance, line combinations, and goalie availability.

---

## Impact Levels

### Player Importance Tiers
| Tier | Position Examples | Typical Impact |
|------|-------------------|----------------|
| **Critical** | #1 Goalie, Top-line Center | 0.3-0.5 goals/game |
| **High** | Top-6 Forward, Top-4 D | 0.15-0.3 goals/game |
| **Medium** | 3rd line, 5/6 D | 0.05-0.15 goals/game |
| **Low** | 4th line, 7th D | < 0.05 goals/game |

### Injury Types
| Type | Typical Duration | Betting Note |
|------|------------------|--------------|
| Day-to-day | 1-3 games | May play, check pregame |
| Week-to-week | 1-3 weeks | Likely out |
| IR (short) | 7+ days | Confirmed out |
| IR (long) | Weeks/months | Season impact |
| LTIR | Extended | Cap implications |

---

## Phase 1: Injury Data Sources

### Task 1.1: Injury Data Structure
**File**: `src/models/injury.py`

```python
"""Injury tracking data models."""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List

class InjuryStatus(Enum):
    """Player injury status."""
    HEALTHY = "healthy"
    DAY_TO_DAY = "day-to-day"
    WEEK_TO_WEEK = "week-to-week"
    IR = "ir"
    LTIR = "ltir"
    OUT = "out"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"

class PlayerTier(Enum):
    """Player importance tier."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Injury:
    """Individual injury record."""
    player_id: int
    player_name: str
    team: str
    position: str
    status: InjuryStatus
    injury_type: str  # "lower-body", "upper-body", "illness", etc.
    injury_date: Optional[date] = None
    expected_return: Optional[date] = None
    player_tier: PlayerTier = PlayerTier.MEDIUM
    
    @property
    def days_out(self) -> Optional[int]:
        """Days since injury."""
        if self.injury_date:
            return (date.today() - self.injury_date).days
        return None
    
    @property
    def is_game_time_decision(self) -> bool:
        """Player might play but uncertain."""
        return self.status in [
            InjuryStatus.DAY_TO_DAY,
            InjuryStatus.QUESTIONABLE,
            InjuryStatus.PROBABLE
        ]

@dataclass
class TeamInjuryReport:
    """All injuries for a team."""
    team: str
    injuries: List[Injury] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def critical_injuries(self) -> List[Injury]:
        return [i for i in self.injuries if i.player_tier == PlayerTier.CRITICAL]
    
    @property
    def total_impact(self) -> float:
        """Estimate total goal impact from injuries."""
        impact_map = {
            PlayerTier.CRITICAL: 0.4,
            PlayerTier.HIGH: 0.2,
            PlayerTier.MEDIUM: 0.1,
            PlayerTier.LOW: 0.03
        }
        return sum(impact_map.get(i.player_tier, 0) for i in self.injuries)
```

### Task 1.2: Injury Scraping (External Source)
NHL doesn't have official injury API. Options:
- Manual tracking
- Third-party injury feeds
- News aggregation

```python
"""Injury data collection (placeholder for external source)."""
from datetime import datetime
from typing import List, Dict

# Store injuries in local JSON for now
INJURY_FILE = "data_files/injuries.json"

def load_injuries() -> Dict[str, List[dict]]:
    """Load current injury data from file."""
    from pathlib import Path
    import json
    
    path = Path(INJURY_FILE)
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_injury(
    player_name: str,
    team: str,
    status: str,
    injury_type: str,
    player_tier: str = "medium"
) -> None:
    """Manually add/update an injury."""
    from pathlib import Path
    import json
    
    injuries = load_injuries()
    
    if team not in injuries:
        injuries[team] = []
    
    # Update or add
    for i, inj in enumerate(injuries[team]):
        if inj["player_name"] == player_name:
            injuries[team][i] = {
                "player_name": player_name,
                "status": status,
                "injury_type": injury_type,
                "player_tier": player_tier,
                "updated": datetime.now().isoformat()
            }
            break
    else:
        injuries[team].append({
            "player_name": player_name,
            "status": status,
            "injury_type": injury_type,
            "player_tier": player_tier,
            "updated": datetime.now().isoformat()
        })
    
    Path(INJURY_FILE).parent.mkdir(exist_ok=True)
    Path(INJURY_FILE).write_text(json.dumps(injuries, indent=2))
```

---

## Phase 2: Injury Impact Model

### Task 2.1: Calculate Lineup Impact
**File**: `src/models/injury_impact.py`

```python
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
```

### Task 2.2: Adjust Predictions
```python
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
    
    # Boost for opponent's defensive injuries
    adjusted += opponent_injuries.defensive_impact
    
    return max(0.5, round(adjusted, 2))  # Floor at 0.5 xG
```

---

## Phase 3: Streamlit Integration

### Task 3.1: Injury Dashboard
**File**: `src/pages/8_🏥_Injuries.py`

```python
"""Injury tracking dashboard."""
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Injury Report", page_icon="🏥", layout="wide")
st.title("🏥 Injury Report")

# Team selector
teams = ["TOR", "MTL", "BOS", "NYR"]  # Add all teams
selected_team = st.selectbox("Select Team", teams)

# Current injuries table
st.subheader(f"{selected_team} Current Injuries")

# Placeholder data - replace with actual injury data
injuries_df = pd.DataFrame({
    "Player": ["Player A", "Player B"],
    "Position": ["C", "D"],
    "Status": ["IR", "Day-to-Day"],
    "Injury": ["Lower-body", "Upper-body"],
    "Tier": ["High", "Medium"],
    "Impact": ["-0.20 GF", "-0.08 GF"],
    "Est. Return": ["2 weeks", "Unknown"]
})

st.dataframe(injuries_df, use_container_width=True, hide_index=True)

# Impact summary
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Offensive Impact", "-0.28 GF/G")
with col2:
    st.metric("Defensive Impact", "+0.12 GA/G")
with col3:
    st.metric("Net Impact", "-0.40 goals")

# Add injury form
st.subheader("Add/Update Injury")
with st.form("add_injury"):
    col1, col2 = st.columns(2)
    with col1:
        player_name = st.text_input("Player Name")
        position = st.selectbox("Position", ["C", "LW", "RW", "D", "G"])
        injury_type = st.text_input("Injury Type", "Lower-body")
    with col2:
        status = st.selectbox("Status", ["Day-to-Day", "Week-to-Week", "IR", "LTIR", "Out"])
        tier = st.selectbox("Player Tier", ["Critical", "High", "Medium", "Low"])
    
    if st.form_submit_button("Save Injury"):
        st.success(f"Added injury for {player_name}")
        # TODO: Save to injuries.json
```

---

## Game Day Usage

### Pre-game Injury Check
```python
def pregame_injury_summary(home_team: str, away_team: str) -> dict:
    """Get injury summary for game preview."""
    home_injuries = load_team_injuries(home_team)
    away_injuries = load_team_injuries(away_team)
    
    home_impact = calculate_injury_impact(home_injuries)
    away_impact = calculate_injury_impact(away_injuries)
    
    # Which team has injury advantage?
    advantage = home_impact.net_impact - away_impact.net_impact
    
    return {
        "home_key_out": home_impact.key_injuries,
        "away_key_out": away_impact.key_injuries,
        "home_impact": home_impact.net_impact,
        "away_impact": away_impact.net_impact,
        "injury_edge": "Home" if advantage > 0.1 else "Away" if advantage < -0.1 else "Even",
        "edge_magnitude": abs(advantage)
    }
```

---

## Next Steps
- Connect to [02-modeling.md](02-modeling.md) prediction adjustments
- See [07-line-movement.md](07-line-movement.md) for injury impact on lines
