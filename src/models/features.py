"""Feature engineering for ML models."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime, timedelta

class NHLFeatureEngineer:
    """Feature engineering for NHL game prediction models."""

    def __init__(self):
        self.historical_data_path = Path("data_files/historical")
        self.cache_path = Path("data_files/cache")

    def load_historical_games(self, seasons: List[str] = None) -> pd.DataFrame:
        """
        Load historical game data from multiple seasons.

        Args:
            seasons: List of season strings (e.g., ['2023-24', '2024-25'])

        Returns:
            DataFrame with historical game data
        """
        if seasons is None:
            seasons = ['2023-24', '2024-25']  # Default to last 2 complete seasons

        all_games = []

        for season in seasons:
            season_path = self.historical_data_path / season / "games.json"
            if season_path.exists():
                with open(season_path, 'r') as f:
                    games = json.load(f)
                    for game in games:
                        game['season'] = season
                        all_games.append(game)

        df = pd.DataFrame(all_games)

        # Clean and prepare data
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['date', 'game_id']).reset_index(drop=True)
        
        # Remove duplicates by game_id (keep first occurrence)
        df = df.drop_duplicates(subset='game_id', keep='first')

        return df

    def load_team_stats(self, season: str = "20252026") -> Dict[str, Dict]:
        """
        Load team statistics for a season.

        Args:
            season: Season ID (e.g., "20252026")

        Returns:
            Dictionary mapping team abbreviations to their stats
        """
        stats_file = self.cache_path / f"api.nhle.com_stats_rest_en_team_summary_cayenneExp=seasonId={season}.json"

        if not stats_file.exists():
            return {}

        with open(stats_file, 'r') as f:
            data = json.load(f)

        team_stats = {}
        for team in data.get('data', []):
            # Extract team abbreviation from teamFullName or use teamId as fallback
            team_name = team.get('teamFullName', '').upper()
            if 'CANADIENS' in team_name:
                abbrev = 'MTL'
            elif 'MAPLE LEAFS' in team_name:
                abbrev = 'TOR'
            elif 'CANUCKS' in team_name:
                abbrev = 'VAN'
            elif 'OILERS' in team_name:
                abbrev = 'EDM'
            elif 'FLAMES' in team_name:
                abbrev = 'CGY'
            elif 'JETS' in team_name:
                abbrev = 'WPG'
            elif 'SENATORS' in team_name:
                abbrev = 'OTT'
            elif 'BRUINS' in team_name:
                abbrev = 'BOS'
            elif 'SABRES' in team_name:
                abbrev = 'BUF'
            elif 'RED WINGS' in team_name:
                abbrev = 'DET'
            elif 'PANTHERS' in team_name:
                abbrev = 'FLA'
            elif 'CANADIENS' in team_name:
                abbrev = 'MTL'
            elif 'LIGHTNING' in team_name:
                abbrev = 'TBL'
            elif 'HURRICANES' in team_name:
                abbrev = 'CAR'
            elif 'BLUE JACKETS' in team_name:
                abbrev = 'CBJ'
            elif 'DEVILS' in team_name:
                abbrev = 'NJD'
            elif 'ISLANDERS' in team_name:
                abbrev = 'NYI'
            elif 'RANGERS' in team_name:
                abbrev = 'NYR'
            elif 'FLYERS' in team_name:
                abbrev = 'PHI'
            elif 'PENGUINS' in team_name:
                abbrev = 'PIT'
            elif 'CAPITALS' in team_name:
                abbrev = 'WSH'
            elif 'BLACKHAWKS' in team_name:
                abbrev = 'CHI'
            elif 'STARS' in team_name:
                abbrev = 'DAL'
            elif 'WILD' in team_name:
                abbrev = 'MIN'
            elif 'PREDATORS' in team_name:
                abbrev = 'NSH'
            elif 'BLUES' in team_name:
                abbrev = 'STL'
            elif 'AVALANCHE' in team_name:
                abbrev = 'COL'
            elif 'GOLDEN KNIGHTS' in team_name:
                abbrev = 'VGK'
            elif 'KINGS' in team_name:
                abbrev = 'LAK'
            elif 'DUCKS' in team_name:
                abbrev = 'ANA'
            elif 'COYOTES' in team_name:
                abbrev = 'ARI'
            elif 'SHARKS' in team_name:
                abbrev = 'SJS'
            elif 'KRaken' in team_name.upper():
                abbrev = 'SEA'
            else:
                # Fallback: take first 3 letters
                abbrev = team_name.replace(' ', '')[:3]

            team_stats[abbrev] = {
                'goals_for_pg': team.get('goalsForPerGame', 3.0),
                'goals_against_pg': team.get('goalsAgainstPerGame', 3.0),
                'pp_pct': team.get('powerPlayPct', 20.0) / 100.0,
                'pk_pct': team.get('penaltyKillPct', 80.0) / 100.0,
                'win_pct': team.get('pointPctg', 0.5),
                'games_played': team.get('gamesPlayed', 0)
            }

        return team_stats

    def compute_team_stats_up_to(self, team: str, game_date: datetime, games_df: pd.DataFrame) -> Dict:
        """
        Compute team statistics up to a given date from historical games.

        Args:
            team: Team abbreviation
            game_date: Date up to which to compute stats
            games_df: Historical games DataFrame

        Returns:
            Dictionary with team statistics
        """
        # Get all games for this team before the target date
        team_games = games_df[
            ((games_df['home_team'] == team) | (games_df['away_team'] == team)) &
            (games_df['date'] < game_date)
        ]

        if team_games.empty:
            return {
                'goals_for_pg': 3.0,
                'goals_against_pg': 3.0,
                'pp_pct': 0.20,
                'pk_pct': 0.80,
                'win_pct': 0.5,
                'games_played': 0
            }

        wins = 0
        total_goals_for = 0
        total_goals_against = 0
        total_pp_opportunities = 0
        total_pp_goals = 0
        total_pk_opportunities = 0
        total_pk_goals_against = 0

        for _, game in team_games.iterrows():
            is_home = game['home_team'] == team
            team_score = game['home_score'] if is_home else game['away_score']
            opp_score = game['away_score'] if is_home else game['home_score']

            total_goals_for += team_score
            total_goals_against += opp_score

            if team_score > opp_score:
                wins += 1

            # Estimate power play/penalty kill stats (simplified)
            # In a real implementation, you'd need detailed play-by-play data
            # For now, use reasonable defaults based on game outcome
            total_pp_opportunities += 3  # Rough estimate
            total_pp_goals += max(0, team_score - 2)  # Rough estimate
            total_pk_opportunities += 3  # Rough estimate
            total_pk_goals_against += max(0, opp_score - 2)  # Rough estimate

        n_games = len(team_games)

        return {
            'goals_for_pg': total_goals_for / n_games,
            'goals_against_pg': total_goals_against / n_games,
            'pp_pct': total_pp_goals / total_pp_opportunities if total_pp_opportunities > 0 else 0.20,
            'pk_pct': 1.0 - (total_pk_goals_against / total_pk_opportunities) if total_pk_opportunities > 0 else 0.80,
            'win_pct': wins / n_games,
            'games_played': n_games
        }

    def calculate_recent_form(self, games_df: pd.DataFrame, team: str, game_date: datetime, window: int = 10) -> Dict:
        """
        Calculate recent form metrics for a team.

        Args:
            games_df: Historical games DataFrame
            team: Team abbreviation
            game_date: Date of the game to predict
            window: Number of recent games to consider

        Returns:
            Dictionary with recent form metrics
        """
        # Get games before the target date
        team_games = games_df[
            ((games_df['home_team'] == team) | (games_df['away_team'] == team)) &
            (games_df['date'] < game_date)
        ].tail(window)

        if team_games.empty:
            return {
                'recent_win_pct': 0.5,
                'recent_goals_for_pg': 3.0,
                'recent_goals_against_pg': 3.0,
                'recent_home_win_pct': 0.5,
                'recent_away_win_pct': 0.5,
                'games_in_window': 0
            }

        wins = 0
        home_wins = 0
        away_wins = 0
        home_games = 0
        away_games = 0
        total_goals_for = 0
        total_goals_against = 0

        for _, game in team_games.iterrows():
            is_home = game['home_team'] == team
            team_score = game['home_score'] if is_home else game['away_score']
            opp_score = game['away_score'] if is_home else game['home_score']

            total_goals_for += team_score
            total_goals_against += opp_score

            if team_score > opp_score:
                wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1

            if is_home:
                home_games += 1
            else:
                away_games += 1

        return {
            'recent_win_pct': wins / len(team_games),
            'recent_goals_for_pg': total_goals_for / len(team_games),
            'recent_goals_against_pg': total_goals_against / len(team_games),
            'recent_home_win_pct': home_wins / home_games if home_games > 0 else 0.5,
            'recent_away_win_pct': away_wins / away_games if away_games > 0 else 0.5,
            'games_in_window': len(team_games)
        }

    def calculate_rest_advantage(self, games_df: pd.DataFrame, home_team: str, away_team: str, game_date: datetime) -> Dict:
        """
        Calculate rest advantage based on recent game schedules.

        Args:
            games_df: Historical games DataFrame
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            game_date: Date of the game

        Returns:
            Dictionary with rest metrics
        """
        # Find last game for each team
        home_last_game = games_df[
            ((games_df['home_team'] == home_team) | (games_df['away_team'] == home_team)) &
            (games_df['date'] < game_date)
        ]['date'].max()

        away_last_game = games_df[
            ((games_df['home_team'] == away_team) | (games_df['away_team'] == away_team)) &
            (games_df['date'] < game_date)
        ]['date'].max()

        home_rest_days = (game_date - home_last_game).days - 1 if home_last_game else 7
        away_rest_days = (game_date - away_last_game).days - 1 if away_last_game else 7

        return {
            'home_rest_days': max(0, min(home_rest_days, 7)),  # Cap at 7 days
            'away_rest_days': max(0, min(away_rest_days, 7)),
            'rest_advantage': home_rest_days - away_rest_days,  # Positive = home advantage
            'is_home_back_to_back': home_rest_days == 0,
            'is_away_back_to_back': away_rest_days == 0
        }

    def create_game_features(self, game: Dict, games_df: pd.DataFrame, home_stats: Dict, away_stats: Dict) -> Dict:
        """
        Create simplified feature vector for a game.

        Args:
            game: Game dictionary with home_team, away_team, date, etc.
            games_df: Historical games DataFrame
            home_stats: Pre-computed home team statistics
            away_stats: Pre-computed away team statistics

        Returns:
            Dictionary of features for ML model
        """
        # Simplified features - just basic team stats
        features = {
            # Team strength indicators
            'home_goal_diff': home_stats['goals_for_pg'] - home_stats['goals_against_pg'],
            'away_goal_diff': away_stats['goals_for_pg'] - away_stats['goals_against_pg'],
            'home_pp_pct': home_stats['pp_pct'],
            'away_pp_pct': away_stats['pp_pct'],
            'home_pk_pct': home_stats['pk_pct'],
            'away_pk_pct': away_stats['pk_pct'],
            'home_win_pct': home_stats['win_pct'],
            'away_win_pct': away_stats['win_pct'],

            # Derived features
            'goal_diff_advantage': (home_stats['goals_for_pg'] - home_stats['goals_against_pg']) - (away_stats['goals_for_pg'] - away_stats['goals_against_pg']),
            'win_pct_advantage': home_stats['win_pct'] - away_stats['win_pct'],
            'pp_pct_advantage': home_stats['pp_pct'] - away_stats['pp_pct'],
            'pk_pct_advantage': home_stats['pk_pct'] - away_stats['pk_pct'],
        }

        return features

    def prepare_training_data(self, seasons: List[str] = None, min_games: int = 20) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from historical games.

        Args:
            seasons: List of seasons to include
            min_games: Minimum games played by teams to include

        Returns:
            Tuple of (features_df, targets_series)
        """
        games_df = self.load_historical_games(seasons)

        features_list = []
        targets = []

        for _, game in games_df.iterrows():
            game_date = pd.to_datetime(game['date'])

            # Compute team stats up to this game date (no data leakage)
            home_stats = self.compute_team_stats_up_to(game['home_team'], game_date, games_df)
            away_stats = self.compute_team_stats_up_to(game['away_team'], game_date, games_df)

            # Skip games where teams haven't played enough games yet
            if home_stats['games_played'] < min_games or away_stats['games_played'] < min_games:
                continue

            try:
                features = self.create_game_features(game, games_df, home_stats, away_stats)
                features_list.append(features)
                targets.append(int(game['home_won']))
            except Exception as e:
                print(f"Error processing game {game['game_id']}: {e}")
                continue

        features_df = pd.DataFrame(features_list)
        targets_series = pd.Series(targets, name='home_win')

        return features_df, targets_series