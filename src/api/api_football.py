"""API-Football client"""
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from .rate_limiter import RateLimiter
from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# League-specific season calculation
# Liga MX and other leagues with split seasons use current year for both Apertura and Clausura
LEAGUES_WITH_SPLIT_SEASONS = {
    262,  # Liga MX (Apertura: Jul-Dec, Clausura: Jan-May)
}


class APIFootballClient:
    """Client for API-Football (RapidAPI)"""

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        """Initialize API client"""
        if not Config.RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY not configured")

        self.headers = {
            "x-apisports-key": Config.RAPIDAPI_KEY
        }

        # Rate limiter: PRO plan = 300 requests per minute (7,500/day)
        # Using conservative 250/min to have margin
        self.rate_limiter = RateLimiter(max_requests=250, time_window=60)

        logger.debug("API-Football client initialized")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to API-Football

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

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            logger.debug(f"Making request to {endpoint} with params {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check API response
            if "errors" in data and data["errors"]:
                logger.error(f"API returned errors: {data['errors']}")
                raise Exception(f"API Error: {data['errors']}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_fixtures(
        self,
        league_id: int,
        season: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: str = "NS"  # NS = Not Started
    ) -> List[Dict]:
        """
        Get fixtures for a league

        Args:
            league_id: League ID
            season: Season year (e.g., 2024)
            date_from: Date from (YYYY-MM-DD)
            date_to: Date to (YYYY-MM-DD)
            status: Fixture status (NS, LIVE, FT, etc.)

        Returns:
            List of fixtures
        """
        params = {
            "league": league_id,
            "status": status
        }

        if season:
            params["season"] = season
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to

        logger.info(f"Fetching fixtures for league {league_id}")
        response = self._make_request("fixtures", params)

        return response.get("response", [])

    def get_upcoming_fixtures(
        self,
        league_ids: List[int],
        hours_ahead: int = 72
    ) -> List[Dict]:
        """
        Get upcoming fixtures for multiple leagues

        Args:
            league_ids: List of league IDs
            hours_ahead: Look ahead this many hours

        Returns:
            List of upcoming fixtures
        """
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        date_from = now.strftime("%Y-%m-%d")
        date_to = (now + timedelta(hours=hours_ahead)).strftime("%Y-%m-%d")

        current_month = now.month
        current_year = now.year

        # Default season calculation (European leagues: Aug-May)
        if current_month >= 8:  # Aug-Dec: use current year as season
            default_season = current_year
        else:  # Jan-Jul: use previous year as season
            default_season = current_year - 1

        all_fixtures = []

        for league_id in league_ids:
            try:
                # Use league-specific season calculation
                if league_id in LEAGUES_WITH_SPLIT_SEASONS:
                    # Liga MX and similar: always use current year
                    season = current_year
                    logger.debug(f"League {league_id} uses split-season format, using year {season}")
                else:
                    # Standard European format
                    season = default_season

                fixtures = self.get_fixtures(
                    league_id=league_id,
                    season=season,
                    date_from=date_from,
                    date_to=date_to,
                    status="NS"
                )
                all_fixtures.extend(fixtures)
                logger.info(f"Found {len(fixtures)} upcoming fixtures for league {league_id} (season {season})")
            except Exception as e:
                logger.error(f"Failed to fetch fixtures for league {league_id}: {e}")

        return all_fixtures

    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """
        Get statistics for a specific fixture

        Args:
            fixture_id: Fixture ID

        Returns:
            Fixture statistics
        """
        logger.info(f"Fetching statistics for fixture {fixture_id}")
        response = self._make_request("fixtures/statistics", {"fixture": fixture_id})

        return response.get("response", {})

    def get_odds(
        self,
        fixture_id: int,
        bookmaker: Optional[str] = None,
        bet_type: str = "1"  # 1 = Match Winner (1X2)
    ) -> List[Dict]:
        """
        Get odds for a fixture

        Args:
            fixture_id: Fixture ID
            bookmaker: Bookmaker name (optional)
            bet_type: Bet type ID (1 = 1X2)

        Returns:
            List of odds from different bookmakers
        """
        params = {
            "fixture": fixture_id,
            "bet": bet_type
        }

        if bookmaker:
            params["bookmaker"] = bookmaker

        logger.info(f"Fetching odds for fixture {fixture_id}")
        response = self._make_request("odds", params)

        return response.get("response", [])

    def get_team_statistics(
        self,
        team_id: int,
        league_id: int,
        season: int
    ) -> Dict:
        """
        Get team statistics for a season

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year

        Returns:
            Team statistics
        """
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        logger.info(f"Fetching statistics for team {team_id}")
        response = self._make_request("teams/statistics", params)

        return response.get("response", {})

    def get_predictions(self, fixture_id: int) -> Dict:
        """
        Get AI predictions from API-Football

        Args:
            fixture_id: Fixture ID

        Returns:
            Predictions data
        """
        logger.info(f"🚀 get_predictions METHOD CALLED for fixture {fixture_id}")
        params = {"fixture": fixture_id}

        logger.info(f"Fetching predictions for fixture {fixture_id}")

        try:
            response = self._make_request("predictions", params)
            logger.debug(f"Predictions API response keys: {list(response.keys())}")

            # The response is a dict with "response" key containing a list
            predictions_list = response.get("response", [])
            logger.debug(f"Predictions list type: {type(predictions_list)}, length: {len(predictions_list) if isinstance(predictions_list, list) else 'not a list'}")

            if predictions_list and len(predictions_list) > 0:
                logger.info(f"✅ Predictions found for fixture {fixture_id}")
                first_pred = predictions_list[0]
                logger.debug(f"Prediction keys: {list(first_pred.keys())}")
                return first_pred
            else:
                logger.warning(f"⚠️ No predictions available for fixture {fixture_id}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error fetching predictions: {e}")
            return {}

    def get_h2h(
        self,
        team1_id: int,
        team2_id: int,
        last: int = 5
    ) -> List[Dict]:
        """
        Get head-to-head matches between two teams

        Args:
            team1_id: First team ID
            team2_id: Second team ID
            last: Number of last matches

        Returns:
            List of H2H matches
        """
        params = {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last
        }

        logger.info(f"Fetching H2H for teams {team1_id} vs {team2_id}")
        response = self._make_request("fixtures/headtohead", params)

        return response.get("response", [])

    def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """
        Get league standings

        Args:
            league_id: League ID
            season: Season year

        Returns:
            League standings
        """
        params = {
            "league": league_id,
            "season": season
        }

        logger.info(f"Fetching standings for league {league_id}")
        response = self._make_request("standings", params)

        return response.get("response", [])
