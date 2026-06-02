# NHL Hockey Predictions — 6-Month Feature Roadmap

## Month 1: Game Day Experience

- **Today's games page overhaul** — Matchup cards with: model win %, puck line coverage %, O/U prediction, goalie confirmed indicator.
- **Injury report banner** — Pull latest injury/out statuses from ESPN or NHL API; flag games with key absences.
- **Back-to-back alert** — Visual badge when a team is on B2B with no rest advantage.
- **Weather/travel notes** — Flag cross-country flights (West Coast to East Coast in <24 hours).

## Month 2: Team Analytics

- **Analytics dashboard** — Team-level xGF%, CF%, PP%, PK% in a sortable table.
- **Form guide** — Last 10 game results with xG differential chart.
- **Division race tracker** — Points standings with model-implied odds of winning each division.
- **Trade deadline impact** — Manual flag when a team makes a significant acquisition.

## Month 3: Player Props

- **Goal scorer props** — Compare model's expected goals per player to DraftKings anytime goal scorer market.
- **Assist props** — Primary point projections vs. DraftKings assist market.
- **Goalie performance props** — Model save % projection vs. DraftKings saves market.

## Month 4: Historical Analysis

- **Season comparison page** — Compare this season's team stats to prior 3 seasons.
- **Playoffs odds tracker** — Rolling playoff probability for each team using points pace.
- **Head-to-head history** — Last 10 meetings for tonight's matchup.

## Month 5: Betting Tools

- **Puck line value finder** — Filter by puck line edge > 3%.
- **Parlay builder** — Select multiple games; compute implied parlay probability.
- **CLV tracker** — Opening vs. closing lines for this week's games.

## Month 6: Automation

- **Morning email digest** — Day-of game picks sent at 8 AM ET.
- **Nightly data refresh** — GitHub Action fetches new game results and updates analytics cache.
- **Discord game-day picks** — Post top pick for each day's slate.
