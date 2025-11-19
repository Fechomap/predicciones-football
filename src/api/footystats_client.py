"""FootyStats API client"""
import requests
from typing import Dict, List, Optional, Any

from .rate_limiter import RateLimiter
from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FootyStatsClient:
    """Client for FootyStats API"""

    def __init__(self):
        """Initialize FootyStats API client"""
        if not Config.FOOTYSTATS_API_KEY:
            raise ValueError("FOOTYSTATS_API_KEY not configured")

        self.base_url = Config.FOOTYSTATS_BASE_URL
        self.api_key = Config.FOOTYSTATS_API_KEY

        # Rate limiter: Adjust based on your plan
        # Hobby: 1800 requests/hour = 30 requests/minute
        # Serious: 3600 requests/hour = 60 requests/minute
        # Everything: 4500 requests/hour = 75 requests/minute
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)

        logger.debug("FootyStats client initialized")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to FootyStats API

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            requests.RequestException: On request failure
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Add API key to params
        if params is None:
            params = {}
        params['key'] = self.api_key

        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making request to {endpoint}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check API response success
            if not data.get('success', False):
                message = data.get('message', 'Unknown error')
                logger.error(f"FootyStats API error: {message}")
                raise Exception(f"API Error: {message}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_league_matches(
        self,
        league_id: int,
        season_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get matches for a league

        Args:
            league_id: FootyStats league ID
            season_id: Season ID (optional)

        Returns:
            List of match data
        """
        params = {'league_id': league_id}
        if season_id:
            params['season_id'] = season_id

        try:
            logger.info(f"Fetching matches for league {league_id}")
            response = self._make_request('league-matches', params)

            matches = response.get('data', [])
            logger.info(f"Found {len(matches)} matches for league {league_id}")

            return matches

        except Exception as e:
            logger.error(f"Failed to fetch matches: {e}")
            return []

    def get_league_teams(self, league_id: int) -> List[Dict]:
        """
        Get all teams from a league

        Args:
            league_id: FootyStats league ID

        Returns:
            List of teams in the league
        """
        params = {'league_id': league_id}

        try:
            logger.debug(f"Fetching teams for league {league_id}")
            response = self._make_request('league-teams', params)

            teams = response.get('data', [])
            logger.debug(f"Found {len(teams)} teams in league {league_id}")

            return teams

        except Exception as e:
            logger.error(f"Failed to fetch league teams: {e}")
            return []

    def get_team_stats(
        self,
        team_id: int,
        season_id: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get detailed team statistics

        Args:
            team_id: FootyStats team ID
            season_id: Season ID (optional)

        Returns:
            Team statistics data
        """
        params = {'team_id': team_id}
        if season_id:
            params['season_id'] = season_id

        try:
            logger.debug(f"Fetching stats for team {team_id}")
            response = self._make_request('team', params)

            data = response.get('data', {})
            # API sometimes returns list, handle both cases
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data if data else None

        except Exception as e:
            logger.error(f"Failed to fetch team stats: {e}")
            return None

    def get_match_details(
        self,
        match_id: int
    ) -> Optional[Dict]:
        """
        Get detailed match statistics

        Args:
            match_id: FootyStats match ID

        Returns:
            Match details with stats
        """
        params = {'id': match_id}

        try:
            logger.debug(f"Fetching details for match {match_id}")
            response = self._make_request('match', params)

            data = response.get('data', {})
            return data if data else None

        except Exception as e:
            logger.error(f"Failed to fetch match details: {e}")
            return None

    def get_h2h(
        self,
        team_a_id: int,
        team_b_id: int
    ) -> List[Dict]:
        """
        Get head-to-head matches between two teams

        Args:
            team_a_id: First team ID
            team_b_id: Second team ID

        Returns:
            List of H2H matches
        """
        params = {
            'team_a_id': team_a_id,
            'team_b_id': team_b_id
        }

        try:
            logger.debug(f"Fetching H2H between {team_a_id} and {team_b_id}")
            response = self._make_request('h2h', params)

            matches = response.get('data', [])
            logger.debug(f"Found {len(matches)} H2H matches")

            return matches

        except Exception as e:
            logger.error(f"Failed to fetch H2H: {e}")
            return []

    def get_team_recent_matches(
        self,
        team_id: int,
        league_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent matches for a team from league matches

        Args:
            team_id: FootyStats team ID
            league_id: FootyStats league ID
            limit: Number of recent matches

        Returns:
            List of recent matches
        """
        try:
            # Get all league matches
            all_matches = self.get_league_matches(league_id)

            # Filter matches where team participated
            team_matches = [
                m for m in all_matches
                if m.get('homeID') == team_id or m.get('awayID') == team_id
            ]

            # Sort by date (most recent first) and limit
            team_matches = sorted(
                team_matches,
                key=lambda x: x.get('date_unix', 0),
                reverse=True
            )[:limit]

            logger.debug(f"Found {len(team_matches)} recent matches for team {team_id}")

            return team_matches

        except Exception as e:
            logger.error(f"Failed to get team recent matches: {e}")
            return []

    def calculate_team_averages(self, matches: List[Dict], team_id: int) -> Dict[str, float]:
        """
        Calculate team averages from match data

        Args:
            matches: List of match data
            team_id: Team ID to calculate stats for

        Returns:
            Dictionary with calculated averages
        """
        if not matches:
            return {
                'avg_goals_scored': 0.0,
                'avg_goals_conceded': 0.0,
                'avg_corners': 0.0,
                'avg_shots': 0.0,
                'avg_shots_on_target': 0.0,
                'avg_possession': 0.0,
                'btts_percentage': 0.0,
                'over_25_percentage': 0.0
            }

        total_goals_scored = 0
        total_goals_conceded = 0
        total_corners = 0
        total_shots = 0
        total_shots_on_target = 0
        total_possession = 0
        btts_count = 0
        over_25_count = 0

        for match in matches:
            is_home = match.get('homeID') == team_id

            if is_home:
                total_goals_scored += match.get('homeGoalCount', 0)
                total_goals_conceded += match.get('awayGoalCount', 0)
                total_corners += match.get('team_a_corners', 0)
                total_shots += match.get('team_a_shots', 0)
                total_shots_on_target += match.get('team_a_shotsOnTarget', 0)
                total_possession += match.get('team_a_possession', 0)
            else:
                total_goals_scored += match.get('awayGoalCount', 0)
                total_goals_conceded += match.get('homeGoalCount', 0)
                total_corners += match.get('team_b_corners', 0)
                total_shots += match.get('team_b_shots', 0)
                total_shots_on_target += match.get('team_b_shotsOnTarget', 0)
                total_possession += match.get('team_b_possession', 0)

            # BTTS (Both Teams To Score)
            home_goals = match.get('homeGoalCount', 0)
            away_goals = match.get('awayGoalCount', 0)
            if home_goals > 0 and away_goals > 0:
                btts_count += 1

            # Over 2.5 goals
            total_goals = home_goals + away_goals
            if total_goals > 2.5:
                over_25_count += 1

        num_matches = len(matches)

        return {
            'avg_goals_scored': total_goals_scored / num_matches,
            'avg_goals_conceded': total_goals_conceded / num_matches,
            'avg_corners': total_corners / num_matches,
            'avg_shots': total_shots / num_matches,
            'avg_shots_on_target': total_shots_on_target / num_matches,
            'avg_possession': total_possession / num_matches,
            'btts_percentage': (btts_count / num_matches) * 100,
            'over_25_percentage': (over_25_count / num_matches) * 100
        }
