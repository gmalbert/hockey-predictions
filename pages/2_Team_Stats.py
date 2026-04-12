"""Team statistics and trends."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.api.nhl_client import NHLClient
from footer import add_betting_oracle_footer

st.title("📊 Team Statistics")

# Initialize client
@st.cache_resource
def get_client():
    return NHLClient()

client = get_client()

# Team selector - create list of (full name, abbreviation) tuples
team_options = [(client.TEAM_NAMES.get(abbr, abbr), abbr) for abbr in sorted(client.TEAM_NAMES.keys())]
team_names = [name for name, _ in team_options]
team_abbrevs = [abbr for _, abbr in team_options]

default_idx = team_abbrevs.index("TOR") if "TOR" in team_abbrevs else 0
selected_team_name = st.selectbox("Select Team", team_names, index=default_idx)
selected_team = team_abbrevs[team_names.index(selected_team_name)]

# Get team stats
try:
    team_stats = client.get_team_summary(selected_team)
    
    if team_stats:
        # Tabs for different stat views
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Season Stats", "Recent Games", "Advanced"])

        with tab1:
            st.subheader(f"{team_stats.get('team_full_name', selected_team)} - Season Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                record = f"{team_stats['wins']}-{team_stats['losses']}-{team_stats['ot_losses']}"
                st.metric("Record", record)
            with col2:
                st.metric("Points", team_stats['points'])
            with col3:
                st.metric("Goals For", team_stats['goals_for'])
            with col4:
                st.metric("Goals Against", team_stats['goals_against'])
            
            # Advanced stats
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Goals/Game", f"{team_stats['goals_for_pg']:.2f}")
            with col2:
                st.metric("Goals Against/Game", f"{team_stats['goals_against_pg']:.2f}")
            with col3:
                st.metric("Power Play %", f"{team_stats['pp_pct']:.1%}")
            with col4:
                st.metric("Penalty Kill %", f"{team_stats['pk_pct']:.1%}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Shots For/Game", f"{team_stats['shots_for_pg']:.2f}")
            with col2:
                st.metric("Shots Against/Game", f"{team_stats['shots_against_pg']:.2f}")
        
        with tab2:
            st.subheader("Detailed Statistics")
            
            # Create stats dataframe
            stats_df = pd.DataFrame({
                "Category": [
                    "Games Played",
                    "Wins",
                    "Losses",
                    "OT Losses",
                    "Points",
                    "Goals For",
                    "Goals Against",
                    "Goal Differential",
                    "GF/Game",
                    "GA/Game",
                    "Power Play %",
                    "Penalty Kill %",
                    "Shots For/Game",
                    "Shots Against/Game"
                ],
                "Value": [
                    str(team_stats['games_played']),
                    str(team_stats['wins']),
                    str(team_stats['losses']),
                    str(team_stats['ot_losses']),
                    str(team_stats['points']),
                    str(team_stats['goals_for']),
                    str(team_stats['goals_against']),
                    str(team_stats['goals_for'] - team_stats['goals_against']),
                    f"{team_stats['goals_for_pg']:.2f}",
                    f"{team_stats['goals_against_pg']:.2f}",
                    f"{team_stats['pp_pct']:.1%}",
                    f"{team_stats['pk_pct']:.1%}",
                    f"{team_stats['shots_for_pg']:.2f}",
                    f"{team_stats['shots_against_pg']:.2f}"
                ]
            })
            
            st.dataframe(stats_df, width='stretch', hide_index=True)
        
        with tab3:
            st.subheader("Recent Games")
            
            # Get season games
            try:
                games = client.get_season_games(selected_team)
                
                if games:
                    # Take last 10 games
                    recent_games = games[-10:]
                    
                    games_df = pd.DataFrame([
                        {
                            "Date": g["date"][:10] if g.get("date") else "",
                            "Opponent": client.TEAM_NAMES.get(g["opponent"], g["opponent"]),
                            "Location": "Home" if g["home_away"] == "home" else "Away",
                            "Result": g["result"],
                            "Score": f"{g['team_score']}-{g['opponent_score']}"
                        }
                        for g in reversed(recent_games)
                    ])
                    
                    st.dataframe(games_df, width='stretch', hide_index=True)
                    
                    # Calculate recent record
                    wins = sum(1 for g in recent_games if g["result"] == "W")
                    losses = len(recent_games) - wins
                    st.info(f"Last {len(recent_games)} games: {wins}-{losses}")
                else:
                    st.info("No recent games data available.")
            except Exception as e:
                st.warning(f"Unable to load recent games: {e}")

        with tab4:
            st.subheader("Advanced Shot-Quality Analytics")
            st.caption(
                "Data from NHL stats REST API (`team/analytics`). "
                "xGF = expected goals for, FF% = Fenwick-for %. "
                "Both are 5v5 all-situations season totals."
            )

            analytics_error = None
            try:
                all_analytics = client.get_team_analytics(season="20252026")
                team_adv = all_analytics.get(selected_team)
            except Exception as exc:
                all_analytics = {}
                team_adv = None
                analytics_error = str(exc)

            if analytics_error:
                st.warning(f"Could not load analytics data: {analytics_error}")
            elif not team_adv:
                st.info(
                    "Advanced analytics not yet available for this team or season. "
                    "Check back once ~10 games have been played."
                )
            else:
                gp = max(team_adv.get("games_played", 1), 1)

                # Per-game analytics
                xgf_pg = (team_adv["xgf"] / gp) if team_adv.get("xgf") else None
                xga_pg = (team_adv["xga"] / gp) if team_adv.get("xga") else None

                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    if xgf_pg is not None:
                        st.metric(
                            "xGF/Game",
                            f"{xgf_pg:.2f}",
                            help="Expected goals for per game at all strengths.",
                        )
                with col_b:
                    if xga_pg is not None:
                        diff = xgf_pg - xga_pg if xgf_pg is not None else None
                        st.metric(
                            "xGA/Game",
                            f"{xga_pg:.2f}",
                            delta=f"xGdiff {diff:+.2f}" if diff is not None else None,
                            delta_color="normal",
                            help="Expected goals against per game.",
                        )
                with col_c:
                    ff_pct = team_adv.get("ff_pct")
                    if ff_pct is not None:
                        st.metric(
                            "Fenwick For %",
                            f"{ff_pct*100:.1f}%",
                            delta=f"{(ff_pct - 0.50)*100:+.1f}% vs 50",
                            delta_color="normal",
                            help="Unblocked shot attempt share at all strengths. >50% = possession edge.",
                        )
                with col_d:
                    cf_pct = team_adv.get("cf_pct")
                    if cf_pct is not None:
                        st.metric(
                            "Corsi For %",
                            f"{cf_pct*100:.1f}%",
                            delta=f"{(cf_pct - 0.50)*100:+.1f}% vs 50",
                            delta_color="normal",
                            help="All shot attempt share (Corsi). >50% = territory edge.",
                        )

                # xGF% and high danger
                st.divider()
                col_e, col_f, col_g, col_h = st.columns(4)
                with col_e:
                    xgf_pct = team_adv.get("xgf_pct")
                    if xgf_pct is not None:
                        st.metric(
                            "xGF%",
                            f"{xgf_pct*100:.1f}%",
                            delta=f"{(xgf_pct - 0.50)*100:+.1f}%",
                            delta_color="normal",
                            help="Expected goal share. >50% = team driving play.",
                        )
                with col_f:
                    hd_gf = team_adv.get("hd_goals_for")
                    hd_ga = team_adv.get("hd_goals_against")
                    if hd_gf is not None and hd_ga is not None:
                        hd_diff = hd_gf - hd_ga
                        st.metric(
                            "HD Goals Diff",
                            f"{hd_diff:+d}",
                            help="High-danger goal differential (slot + crease area).",
                        )
                with col_g:
                    hd_sf = team_adv.get("hd_shots_for")
                    hd_sa = team_adv.get("hd_shots_against")
                    if hd_sf is not None and hd_sa is not None and (hd_sf + hd_sa) > 0:
                        hd_pct = hd_sf / (hd_sf + hd_sa)
                        st.metric(
                            "HD Shot%",
                            f"{hd_pct*100:.1f}%",
                            help="High-danger shot share. Proxy for cycle and zone quality.",
                        )
                with col_h:
                    sc_gf = team_adv.get("sc_goals_for")
                    sc_ga = team_adv.get("sc_goals_against")
                    if sc_gf is not None and sc_ga is not None:
                        st.metric(
                            "Scoring Chance Diff",
                            f"{sc_gf - sc_ga:+d}",
                            help="Scoring chances for minus against (all season).",
                        )

            # League-wide analytics comparison table
            st.divider()
            st.subheader("📋 League-Wide Analytics Comparison")

            if all_analytics:
                league_rows = []
                for abbrev, adv in all_analytics.items():
                    gp = max(adv.get("games_played", 1), 1)
                    xgf_pg_l = round(adv["xgf"] / gp, 2) if adv.get("xgf") else None
                    xga_pg_l = round(adv["xga"] / gp, 2) if adv.get("xga") else None
                    xgdiff = round(xgf_pg_l - xga_pg_l, 2) if (xgf_pg_l and xga_pg_l) else None
                    ff = adv.get("ff_pct")
                    cf = adv.get("cf_pct")
                    xgf_pct_l = adv.get("xgf_pct")

                    league_rows.append({
                        "Team": abbrev,
                        "GP": gp,
                        "xGF/G": xgf_pg_l,
                        "xGA/G": xga_pg_l,
                        "xG Diff": xgdiff,
                        "FF%": f"{ff*100:.1f}%" if ff is not None else "—",
                        "CF%": f"{cf*100:.1f}%" if cf is not None else "—",
                        "xGF%": f"{xgf_pct_l*100:.1f}%" if xgf_pct_l is not None else "—",
                    })

                league_df = pd.DataFrame(league_rows)
                if "xG Diff" in league_df.columns:
                    league_df = league_df.sort_values("xG Diff", ascending=False)

                # Highlight selected team
                st.dataframe(
                    league_df,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Team": st.column_config.TextColumn("Team", width="small"),
                        "GP": st.column_config.NumberColumn("GP", width="small"),
                        "xGF/G": st.column_config.NumberColumn("xGF/G", width="small", format="%.2f"),
                        "xGA/G": st.column_config.NumberColumn("xGA/G", width="small", format="%.2f"),
                        "xG Diff": st.column_config.NumberColumn("xG Diff/G", width="small", format="%+.2f"),
                        "FF%": st.column_config.TextColumn("FF%", width="small",
                            help="Fenwick-for %. >50% = possession edge."),
                        "CF%": st.column_config.TextColumn("CF%", width="small"),
                        "xGF%": st.column_config.TextColumn("xGF%", width="small"),
                    },
                )
            else:
                st.info("Analytics data not available.")

            with st.expander("📚 Analytics Glossary"):
                st.markdown("""
                | Metric | Definition | Betting Use |
                |--------|-----------|-------------|
                | **xGF/G** | Expected goals for per game (shot quality adjusted) | Primary model input |
                | **xGA/G** | Expected goals against per game | Defensive quality |
                | **xG Diff** | xGF/G − xGA/G | Positive = team creates more than they allow |
                | **FF%** | Fenwick-for % (all ubl. shot attempts) | Possession proxy; >50% = driving play |
                | **CF%** | Corsi-for % (all shot attempts incl. blocked) | Territory control |
                | **xGF%** | Expected goal share (xGF / (xGF+xGA)) | Best single shot-quality measure |
                | **HD Shot%** | High-danger shot share (slot/crease) | Cycle quality |
                
                **Why these beat raw goals/shots:**  
                A team can lead in raw goals due to shooting luck (shooting 15% vs 8% league avg).
                xG and Fenwick strip out luck and show the *underlying* performance.
                Teams with xGF% > 52% almost always win more over a full season.
                """)
    else:
        st.error(f"No stats available for {selected_team}")
        
except Exception as e:
    st.error(f"Error loading team stats: {e}")

# Add footer
add_betting_oracle_footer()
