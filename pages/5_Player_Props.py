"""Player prop betting analysis."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.title("🎯 Player Props Analysis")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Prop type selector
prop_type = st.selectbox("Stat Type", ["Points", "Goals", "Assists", "Shots", "Saves (Goalies)"])

# Get player stats based on type
st.subheader(f"Top Players by {prop_type}")

try:
    if prop_type == "Saves (Goalies)":
        # Get goalie stats
        players = client.get_goalie_stats(limit=20)
        
        if players:
            player_df = pd.DataFrame([
                {
                    "Rank": idx + 1,
                    "Player": p["name"],
                    "Team": client.TEAM_NAMES.get(p["team"], p["team"]),
                    "GP": p["games_played"],
                    "Wins": p["wins"],
                    "Losses": p["losses"],
                    "OTL": p["ot_losses"],
                    "Save %": f"{p['save_pct']:.3f}",
                    "GAA": f"{p['gaa']:.2f}",
                    "Shutouts": p["shutouts"],
                    "Saves": p["saves"]
                }
                for idx, p in enumerate(players)
            ])
            
            st.dataframe(
                player_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Team": st.column_config.TextColumn("Team", width="medium"),
                    "GP": st.column_config.NumberColumn("Games Played", width="small"),
                    "Wins": st.column_config.NumberColumn("Wins", width="small"),
                    "Losses": st.column_config.NumberColumn("Losses", width="small"),
                    "OTL": st.column_config.NumberColumn("OT Losses", width="small"),
                    "Save %": st.column_config.TextColumn("Save %", width="small"),
                    "GAA": st.column_config.TextColumn("Goals Against Avg", width="small"),
                    "Shutouts": st.column_config.NumberColumn("Shutouts", width="small"),
                    "Saves": st.column_config.NumberColumn("Saves", width="small"),
                }
            )
        else:
            st.info("No goalie stats available.")
    else:
        # Get skater stats
        players = client.get_skater_stats(limit=50)
        
        if players:
            player_df = pd.DataFrame([
                {
                    "Rank": idx + 1,
                    "Player": p["name"],
                    "Team": client.TEAM_NAMES.get(p["team"], p["team"]),
                    "Position": p.get("position", ""),
                    "GP": p["games"],
                    "Goals": p["goals"],
                    "Assists": p["assists"],
                    "Points": p["points"],
                    "Shots": p["shots"],
                    "S%": f"{p['shooting_pct']:.1f}%" if p.get("shooting_pct") else "0%",
                    "TOI/G": f"{p['toi_pg']:.1f}" if p.get("toi_pg") else "0"
                }
                for idx, p in enumerate(players)
            ])
            
            # Sort by selected stat type
            if prop_type == "Points":
                player_df = player_df.sort_values("Points", ascending=False)
            elif prop_type == "Goals":
                player_df = player_df.sort_values("Goals", ascending=False)
            elif prop_type == "Assists":
                player_df = player_df.sort_values("Assists", ascending=False)
            elif prop_type == "Shots":
                player_df = player_df.sort_values("Shots", ascending=False)
            
            # Reset rank after sorting
            player_df["Rank"] = range(1, len(player_df) + 1)
            
            st.dataframe(
                player_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Team": st.column_config.TextColumn("Team", width="medium"),
                    "Position": st.column_config.TextColumn("Pos", width="small"),
                    "GP": st.column_config.NumberColumn("Games Played", width="small"),
                    "Goals": st.column_config.NumberColumn("Goals", width="small"),
                    "Assists": st.column_config.NumberColumn("Assists", width="small"),
                    "Points": st.column_config.NumberColumn("Points", width="small"),
                    "Shots": st.column_config.NumberColumn("Shots", width="small"),
                    "S%": st.column_config.TextColumn("Shooting %", width="small"),
                    "TOI/G": st.column_config.TextColumn("TOI/Game", width="small"),
                }
            )
        else:
            st.info("No player stats available.")
    
    # Player search
    st.divider()
    st.subheader("Player Search")
    player_search = st.text_input("Search by name", placeholder="Enter player name...")
    
    if player_search:
        # Filter players
        if prop_type == "Saves (Goalies)":
            players = client.get_goalie_stats(limit=100)
        else:
            players = client.get_skater_stats(limit=200)
        
        matching = [p for p in players if player_search.lower() in p["name"].lower()]
        
        if matching:
            st.success(f"Found {len(matching)} matching player(s)")
            
            for p in matching[:5]:  # Show first 5 matches
                team_name = client.TEAM_NAMES.get(p['team'], p['team'])
                with st.expander(f"{p['name']} ({team_name})"):
                    if prop_type == "Saves (Goalies)":
                        st.write(f"**Games Played:** {p['games_played']}")
                        st.write(f"**Record:** {p['wins']}-{p['losses']}-{p['ot_losses']}")
                        st.write(f"**Save %:** {p['save_pct']:.3f}")
                        st.write(f"**GAA:** {p['gaa']:.2f}")
                        st.write(f"**Shutouts:** {p['shutouts']}")
                        st.write(f"**Saves:** {p['saves']}")
                    else:
                        st.write(f"**Position:** {p.get('position', 'N/A')}")
                        st.write(f"**Games:** {p['games']}")
                        st.write(f"**Goals:** {p['goals']}")
                        st.write(f"**Assists:** {p['assists']}")
                        st.write(f"**Points:** {p['points']}")
                        st.write(f"**Shots:** {p['shots']}")
                        st.write(f"**+/-:** {p.get('plus_minus', 0)}")
        else:
            st.warning("No players found matching that name.")
            
except Exception as e:
    st.error(f"Error loading player stats: {e}")

# ── Per-60 Analytics ─────────────────────────────────────────────────────────
st.divider()
st.subheader("⚡ Per-60 Rates & Shooting% Regression Watch")
st.caption(
    "Per-60 rates normalise production for players with different ice time. "
    "Shooting% regression flags players who are likely due for a slowdown (or boost)."
)

per60_tab, regression_tab = st.tabs(["Per-60 Rates", "Regression Watch"])

with per60_tab:
    try:
        skater_analytics = client.get_skater_analytics(limit=100)

        if skater_analytics:
            per60_records = [
                {
                    "Player": p["name"],
                    "Team": client.TEAM_NAMES.get(p.get("team", ""), p.get("team", "")),
                    "Pos": p.get("position", ""),
                    "GP": p.get("games", 0),
                    "G/60": round(p.get("g_per_60", 0), 2),
                    "A/60": round(p.get("a_per_60", 0), 2),
                    "P/60": round(p.get("p_per_60", 0), 2),
                    "TOI/G": round(p.get("toi_pg", 0), 1) if p.get("toi_pg") else None,
                }
                for p in skater_analytics
                if p.get("p_per_60") is not None
            ]

            if not per60_records:
                st.info("Per-60 data not available for the current season.")
            else:
                per60_df = pd.DataFrame(per60_records)
                per60_df = per60_df.sort_values("P/60", ascending=False).reset_index(drop=True)
                per60_df.insert(0, "Rank", range(1, len(per60_df) + 1))

                st.dataframe(
                    per60_df,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", width="small"),
                        "Player": st.column_config.TextColumn("Player", width="medium"),
                        "Team": st.column_config.TextColumn("Team", width="small"),
                        "Pos": st.column_config.TextColumn("Pos", width="small"),
                        "GP": st.column_config.NumberColumn("GP", width="small"),
                        "G/60": st.column_config.NumberColumn(
                            "G/60", width="small", format="%.2f",
                            help="Goals per 60 minutes of ice time",
                        ),
                        "A/60": st.column_config.NumberColumn(
                            "A/60", width="small", format="%.2f",
                            help="Assists per 60 minutes of ice time",
                        ),
                        "P/60": st.column_config.NumberColumn(
                            "P/60", width="small", format="%.2f",
                            help="Points per 60 minutes — best measure of scorer quality",
                        ),
                        "TOI/G": st.column_config.NumberColumn("TOI/G", width="small"),
                    },
                )
                with st.expander("Why per-60?"):
                    st.markdown(
                        "Raw totals reward players who log heavy ice time. Per-60 rates "
                        "show **efficiency** — how much a player produces per minute of "
                        "opportunity. A 4th-liner scoring at 1.5 P/60 may be more efficient "
                        "than a 1st-liner at 1.2 P/60 who gets 20+ minutes."
                    )
        else:
            st.info("Per-60 data not available for the current season.")
    except Exception as exc:
        st.warning(f"Could not load per-60 data: {exc}")

with regression_tab:
    st.markdown(
        "Players whose shooting percentage is **≥ 1.5× their career / league-average xG%** "
        "are likely due for regression. Players below **0.7×** are potential positive "
        "regression candidates."
    )
    LEAGUE_AVG_SHOOT_PCT = 0.092  # ~9.2% league average shooting pct

    try:
        skaters = client.get_skater_stats(limit=200)

        if skaters:
            regression_rows = []
            for p in skaters:
                shoot_pct_raw = p.get("shooting_pct")
                if shoot_pct_raw is None:
                    continue
                # shooting_pct comes back as percentage (e.g. 14.5 means 14.5%)
                shoot_pct = shoot_pct_raw / 100.0 if shoot_pct_raw > 1.0 else shoot_pct_raw
                if p.get("shots", 0) < 20:
                    continue  # too small a sample

                ratio = shoot_pct / LEAGUE_AVG_SHOOT_PCT
                if ratio >= 1.5 or ratio <= 0.7:
                    regression_rows.append({
                        "Player": p["name"],
                        "Team": client.TEAM_NAMES.get(p.get("team", ""), p.get("team", "")),
                        "GP": p.get("games", 0),
                        "Goals": p.get("goals", 0),
                        "Shots": p.get("shots", 0),
                        "S%": f"{shoot_pct*100:.1f}%",
                        "Lg Avg S%": f"{LEAGUE_AVG_SHOOT_PCT*100:.1f}%",
                        "Ratio": round(ratio, 2),
                        "Signal": "🔴 Due to cool off" if ratio >= 1.5 else "🟢 Positive regression cand.",
                    })

            if regression_rows:
                reg_df = (
                    pd.DataFrame(regression_rows)
                    .sort_values("Ratio", ascending=False)
                    .reset_index(drop=True)
                )
                st.dataframe(reg_df, hide_index=True, width="stretch")
            else:
                st.success("No strong regression candidates at this time.")
        else:
            st.info("No skater data available for regression analysis.")
    except Exception as exc:
        st.warning(f"Could not load regression data: {exc}")

    with st.expander("How regression watch works"):
        st.markdown(f"""
        **Rule of thumb:**
        - Shooting% ≥ **{LEAGUE_AVG_SHOOT_PCT*1.5*100:.0f}%** (1.5× league avg {LEAGUE_AVG_SHOOT_PCT*100:.1f}%): 
          Player is likely riding hot goaltending luck or unsustainable heat — expect fewer goals soon.
        - Shooting% ≤ **{LEAGUE_AVG_SHOOT_PCT*0.7*100:.1f}%** (0.7× league avg): 
          Player may be running cold; goals likely coming once shooting luck normalises.
        
        This is most useful for **prop bets on goal totals** — a player at 19% shooting will 
        almost always cool off, making the "Over" on his goals props risky.
        
        Players with fewer than 20 shots are excluded (sample too small).
        """)

# Add footer
add_betting_oracle_footer()
