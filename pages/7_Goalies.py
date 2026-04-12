"""Goalie analysis and matchup comparison page."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.api.nhl_client import NHLClient
from src.models.goalie_adjustment import (
    calculate_goalie_adjustment,
    calculate_goalie_adjustment_with_analytics,
    adjusted_xg_for_matchup,
    adjusted_xg_with_analytics,
    LEAGUE_AVG_SAVE_PCT,
)
from src.models.goalie_matchup import compare_goalie_matchup, goalie_recent_form
from footer import add_betting_oracle_footer

st.title("🥅 Goalie Analysis")
st.markdown("Analyze goalie matchups and their impact on betting value.")

# Initialize client for team names
client = NHLClient()

# Fetch goalie stats first
try:
    import httpx
    url = "https://api.nhle.com/stats/rest/en/goalie/summary"
    params = {
        "cayenneExp": "seasonId=20252026",
        "sort": "savePct",
        "direction": "DESC",
        "limit": 100
    }
    
    with httpx.Client(timeout=10.0) as http_client:
        response = http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Build goalie dictionary
    goalie_stats = {}
    goalie_names = []
    for g in data.get("data", []):
        if g.get("gamesPlayed", 0) >= 5:  # Minimum 5 games
            name = g.get("goalieFullName", "Unknown")
            team = g.get("teamAbbrevs", "")
            display_name = f"{name} ({team})"
            goalie_names.append(display_name)
            goalie_stats[display_name] = {
                "name": name,
                "team": team,
                "sv_pct": g.get("savePct", 0.900),
                "games": g.get("gamesPlayed", 0),
                "wins": g.get("wins", 0),
                "gaa": g.get("goalsAgainstAverage", 0),
                "shutouts": g.get("shutouts", 0)
            }
    
    if not goalie_names:
        st.error("No goalie data available")
        st.stop()
        
except Exception as e:
    st.error(f"Could not load goalie data: {e}")
    st.stop()

# Fetch goalie analytics (GSAA, HD SV%, danger-zone saves)
goalie_analytics: dict[str, dict] = {}
try:
    advanced_data = client.get_goalie_analytics(season="20252026", limit=100)
    for row in advanced_data:
        n = row.get("name", "")
        goalie_analytics[n] = row
except Exception:
    pass  # Analytics gracefully optional

# Quick Goalie Comparison
st.subheader("Goalie Matchup Comparison")

st.info("""
💡 **Tip**: Select two goalies below to compare their stats and see the betting edge.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏠 Home Goalie")
    goalie_1_select = st.selectbox(
        "Select Goalie",
        options=goalie_names,
        key="goalie_1",
        index=0
    )
    
    goalie_1 = goalie_stats[goalie_1_select]
    g1_analytics = goalie_analytics.get(goalie_1["name"], {})

    # Calculate adjustment (use analytics when available)
    goalie_1_adj = calculate_goalie_adjustment_with_analytics(
        goalie_name=goalie_1["name"],
        save_pct=goalie_1["sv_pct"],
        sample_size=goalie_1["games"],
        gsaa=g1_analytics.get("gsaa"),
        hd_save_pct=g1_analytics.get("hd_save_pct"),
    )
    
    # Display stats
    st.markdown(f"**{goalie_1['team']}** - {goalie_1['games']} GP")
    
    col1a, col1b, col1c = st.columns(3)
    with col1a:
        st.metric("SV%", f"{goalie_1['sv_pct']:.3f}")
    with col1b:
        st.metric("GAA", f"{goalie_1['gaa']:.2f}")
    with col1c:
        st.metric("W-SO", f"{goalie_1['wins']}-{goalie_1['shutouts']}")
    
    col1d, col1e = st.columns(2)
    with col1d:
        st.metric("vs League Avg", f"{(goalie_1['sv_pct'] - LEAGUE_AVG_SAVE_PCT)*100:+.1f}%")
    with col1e:
        st.metric("Goals Saved/Game", f"{goalie_1_adj.adjustment:+.2f}")

    # GSAA and HD metrics (if available)
    if g1_analytics.get("gsaa") is not None:
        col1f, col1g = st.columns(2)
        with col1f:
            st.metric(
                "GSAA (season)",
                f"{g1_analytics['gsaa']:+.2f}",
                help="Goals Saved Above Average — NHL's own metric. Positive = better than average.",
            )
        with col1g:
            if g1_analytics.get("hd_save_pct"):
                st.metric(
                    "HD SV%",
                    f"{g1_analytics['hd_save_pct']:.3f}",
                    delta=f"{(g1_analytics['hd_save_pct'] - 0.830)*100:+.1f}% vs avg",
                    help="High-danger save %. League avg ≈ .830",
                )

    # Confidence indicator
    confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    method_label = {"sv_pct": "SV% only", "blended": "GSAA + SV% blended", "gsaa": "GSAA-primary"}
    st.caption(
        f"{confidence_color.get(goalie_1_adj.confidence, '⚪')} "
        f"Confidence: {goalie_1_adj.confidence.title()} "
        f"({method_label.get(goalie_1_adj.method, goalie_1_adj.method)})"
    )

with col2:
    st.markdown("### ✈️ Away Goalie")
    goalie_2_select = st.selectbox(
        "Select Goalie",
        options=goalie_names,
        key="goalie_2",
        index=min(1, len(goalie_names)-1)
    )
    
    goalie_2 = goalie_stats[goalie_2_select]
    g2_analytics = goalie_analytics.get(goalie_2["name"], {})

    goalie_2_adj = calculate_goalie_adjustment_with_analytics(
        goalie_name=goalie_2["name"],
        save_pct=goalie_2["sv_pct"],
        sample_size=goalie_2["games"],
        gsaa=g2_analytics.get("gsaa"),
        hd_save_pct=g2_analytics.get("hd_save_pct"),
    )
    
    st.markdown(f"**{goalie_2['team']}** - {goalie_2['games']} GP")
    
    col2a, col2b, col2c = st.columns(3)
    with col2a:
        st.metric("SV%", f"{goalie_2['sv_pct']:.3f}")
    with col2b:
        st.metric("GAA", f"{goalie_2['gaa']:.2f}")
    with col2c:
        st.metric("W-SO", f"{goalie_2['wins']}-{goalie_2['shutouts']}")
    
    col2d, col2e = st.columns(2)
    with col2d:
        st.metric("vs League Avg", f"{(goalie_2['sv_pct'] - LEAGUE_AVG_SAVE_PCT)*100:+.1f}%")
    with col2e:
        st.metric("Goals Saved/Game", f"{goalie_2_adj.adjustment:+.2f}")

    if g2_analytics.get("gsaa") is not None:
        col2f, col2g = st.columns(2)
        with col2f:
            st.metric(
                "GSAA (season)",
                f"{g2_analytics['gsaa']:+.2f}",
                help="Goals Saved Above Average — positive = better than average.",
            )
        with col2g:
            if g2_analytics.get("hd_save_pct"):
                st.metric(
                    "HD SV%",
                    f"{g2_analytics['hd_save_pct']:.3f}",
                    delta=f"{(g2_analytics['hd_save_pct'] - 0.830)*100:+.1f}% vs avg",
                    help="High-danger save %. League avg ≈ .830",
                )

    st.caption(
        f"{confidence_color.get(goalie_2_adj.confidence, '⚪')} "
        f"Confidence: {goalie_2_adj.confidence.title()} "
        f"({method_label.get(goalie_2_adj.method, goalie_2_adj.method)})"
    )

# Matchup Analysis
st.markdown("---")
st.subheader("Matchup Edge Analysis")

matchup = compare_goalie_matchup(
    home_goalie_sv_pct=goalie_1["sv_pct"],
    away_goalie_sv_pct=goalie_2["sv_pct"],
    home_goalie_name=goalie_1["name"],
    away_goalie_name=goalie_2["name"]
)

# Display edge
edge_col1, edge_col2, edge_col3 = st.columns([1, 2, 1])

with edge_col2:
    if matchup.edge_team == "Even":
        st.info(f"**⚖️ Matchup is Even**\n\nNo significant goalie advantage ({matchup.edge_magnitude:.2f} goals)")
    elif matchup.edge_team == "Home":
        st.success(f"**🏠 {goalie_1['name']} Advantage**\n\n{matchup.edge_magnitude:.2f} expected goals difference")
    else:
        st.warning(f"**✈️ {goalie_2['name']} Advantage**\n\n{matchup.edge_magnitude:.2f} expected goals difference")

# Expected Goals Adjustment Example
st.markdown("---")
st.subheader("Expected Goals Adjustment")

st.markdown("See how goalie quality affects team expected goals (xG):")

col3, col4 = st.columns(2)

with col3:
    st.markdown(f"#### {goalie_1['team']} Attack (vs {goalie_2['name']})")
    goalie_1_team_xg = st.slider("Base xG (before goalie adj)", 2.0, 4.5, 3.0, 0.1, key="goalie_1_xg")
    
    # Legacy adjustment
    adj_legacy = adjusted_xg_for_matchup(goalie_1_team_xg, goalie_2["sv_pct"], goalie_2["games"])
    # Analytics-enhanced adjustment
    adj_enhanced = adjusted_xg_with_analytics(
        goalie_1_team_xg,
        goalie_2["sv_pct"],
        goalie_2["games"],
        opposing_goalie_name=goalie_2["name"],
        opposing_goalie_gsaa=g2_analytics.get("gsaa"),
        opposing_goalie_hd_sv_pct=g2_analytics.get("hd_save_pct"),
    )
    
    st.metric("Legacy Adjusted xG", f"{adj_legacy:.2f}", delta=f"{adj_legacy - goalie_1_team_xg:+.2f}")
    if g2_analytics.get("gsaa") is not None:
        st.metric(
            "Enhanced Adjusted xG",
            f"{adj_enhanced:.2f}",
            delta=f"{adj_enhanced - goalie_1_team_xg:+.2f}",
            help="Uses GSAA + HD SV% in addition to season SV%.",
        )

with col4:
    st.markdown(f"#### {goalie_2['team']} Attack (vs {goalie_1['name']})")
    goalie_2_team_xg = st.slider("Base xG (before goalie adj)", 2.0, 4.5, 3.0, 0.1, key="goalie_2_xg")
    
    adj_legacy_2 = adjusted_xg_for_matchup(goalie_2_team_xg, goalie_1["sv_pct"], goalie_1["games"])
    adj_enhanced_2 = adjusted_xg_with_analytics(
        goalie_2_team_xg,
        goalie_1["sv_pct"],
        goalie_1["games"],
        opposing_goalie_name=goalie_1["name"],
        opposing_goalie_gsaa=g1_analytics.get("gsaa"),
        opposing_goalie_hd_sv_pct=g1_analytics.get("hd_save_pct"),
    )
    
    st.metric("Legacy Adjusted xG", f"{adj_legacy_2:.2f}", delta=f"{adj_legacy_2 - goalie_2_team_xg:+.2f}")
    if g1_analytics.get("gsaa") is not None:
        st.metric(
            "Enhanced Adjusted xG",
            f"{adj_enhanced_2:.2f}",
            delta=f"{adj_enhanced_2 - goalie_2_team_xg:+.2f}",
            help="Uses GSAA + HD SV% in addition to season SV%.",
        )

# League Goalie Rankings
st.markdown("---")
st.subheader("League Goalie Leaders")

# Build display table — blend summary + analytics
display_goalies = []
for display_name, stats in goalie_stats.items():
    g_analytics = goalie_analytics.get(stats["name"], {})
    display_goalies.append({
        "Goalie": stats["name"],
        "Team": client.TEAM_NAMES.get(stats["team"], stats["team"]),
        "GP": stats["games"],
        "W": stats["wins"],
        "SV%": f"{stats['sv_pct']:.3f}",
        "GAA": f"{stats['gaa']:.2f}",
        "SO": stats["shutouts"],
        "GSAA": f"{g_analytics['gsaa']:+.2f}" if g_analytics.get("gsaa") is not None else "—",
        "HD SV%": f"{g_analytics['hd_save_pct']:.3f}" if g_analytics.get("hd_save_pct") else "—",
    })

df = pd.DataFrame(display_goalies)

# Sort by SV% descending for display
try:
    df = df.sort_values("SV%", ascending=False)
except Exception:
    pass

st.dataframe(
    df.head(30),
    hide_index=True,
    width="stretch",
    column_config={
        "Goalie": st.column_config.TextColumn("Goalie", width="medium"),
        "Team": st.column_config.TextColumn("Team", width="medium"),
        "GP": st.column_config.NumberColumn("GP", width="small"),
        "W": st.column_config.NumberColumn("W", width="small"),
        "SV%": st.column_config.TextColumn("SV%", width="small"),
        "GAA": st.column_config.TextColumn("GAA", width="small"),
        "SO": st.column_config.NumberColumn("SO", width="small"),
        "GSAA": st.column_config.TextColumn(
            "GSAA", width="small",
            help="Goals Saved Above Average (NHL). Positive = better than avg.",
        ),
        "HD SV%": st.column_config.TextColumn(
            "HD SV%", width="small",
            help="High-Danger Save %. League avg ≈ .830.",
        ),
    },
)

# Interpretation Guide
with st.expander("📚 Goalie Analysis Guide"):
    st.markdown("""
    ### Understanding Goalie Impact
    
    **Save Percentage Benchmarks**
    - **Elite (> 0.920)**: Top-tier goalie, significant betting factor
    - **Above Average (0.910-0.920)**: Solid starter, positive impact
    - **League Average (0.900-0.910)**: Typical NHL starter
    - **Below Average (< 0.900)**: Weakness to exploit

    **GSAA — Goals Saved Above Average**
    GSAA is the NHL's own metric: the number of goals saved *above* what an
    average goalie would have saved facing the same shots.
    - **Positive GSAA**: Goalie is outperforming — but large positive values often
      regress toward zero (watch for fade candidates).
    - **Negative GSAA**: Goalie is allowing more goals than expected.
    - Good rule of thumb: > +5 GSAA = legitimate elite; < -5 GSAA = exploitable.

    **HD SV% — High-Danger Save Percentage**
    Shots from the slot and crease area.  League average ≈ .830.
    - Goalies above .860 HD SV% are elite at stopping the most dangerous shots.
    - Goalies below .800 HD SV% are a significant liability; opposing high-danger
      lines are a strong bet in these matchups.

    **Enhanced Adjustment vs Legacy**
    The *Enhanced* model blends GSAA-per-game and HD SV% with the legacy
    SV%-based model.  It is more responsive to current-season performance
    and shot quality, not just raw goals allowed.

    **Betting Implications**
    - ✅ **Bet on team with goalie edge** if line doesn't reflect it
    - ✅ **Fade team with struggling goalie** even if favored
    - ✅ **Look for total value** when elite vs weak goalie
    - ⚠️ **Small samples unreliable** - need 15+ games for confidence
    - ⚠️ **High GSAA regression** — goalies running very hot often cool off
    """)

add_betting_oracle_footer()
