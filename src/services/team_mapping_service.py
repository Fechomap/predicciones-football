"""
Service for managing team ID mappings between API-Football and FootyStats

ARCHITECTURE: ID-CENTRIC (As per PM's recommendation)

This service ONLY reads from database. It does NOT:
- Make API calls to FootyStats
- Perform fuzzy name matching
- Create new mappings dynamically

All team mappings are pre-loaded during onboarding phase using scripts:
- scripts/auto_map_all_teams.py (automatic matching)
- scripts/add_manual_team_mappings.py (manual corrections)

This ensures:
1. 100% predictable behavior
2. No runtime API calls
3. Easy debugging (all mappings visible in database)
4. Scalable to all sports
"""

from typing import Optional
from datetime import datetime

from ..database import db_manager, TeamIDMapping
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TeamMappingService:
    """
    Simple ID translation service - Database lookup ONLY

    Philosophy:
    - Database is the source of truth
    - Mappings are pre-loaded during onboarding
    - Runtime is just a fast DB query (no fuzzy matching)
    - Missing mappings return None (expected for teams not in FootyStats)
    """

    def get_footystats_id(
        self,
        api_football_id: int,
        team_name: str = None,  # DEPRECATED - kept for compatibility
        league_id: int = None   # DEPRECATED - kept for compatibility
    ) -> Optional[int]:
        """
        Get FootyStats ID for an API-Football team

        Strategy:
        1. Query database for mapping
        2. Return footystats_id if found
        3. Return None if not found (team not in FootyStats dataset)

        Args:
            api_football_id: Team ID from API-Football
            team_name: DEPRECATED - no longer used
            league_id: DEPRECATED - no longer used

        Returns:
            FootyStats team ID or None if not mapped
        """
        try:
            with db_manager.get_session() as session:
                mapping = session.query(TeamIDMapping).filter_by(
                    api_football_id=api_football_id
                ).first()

                if not mapping:
                    logger.debug(f"No mapping found for API-Football team {api_football_id}")
                    return None

                if not mapping.footystats_id:
                    logger.debug(f"Team {mapping.team_name} has no FootyStats equivalent (expected)")
                    return None

                logger.debug(
                    f"✅ Mapped: {mapping.team_name} (API:{api_football_id} → FS:{mapping.footystats_id}, "
                    f"conf:{mapping.confidence_score:.0%})"
                )

                return mapping.footystats_id

        except Exception as e:
            logger.error(f"Error getting FootyStats ID for team {api_football_id}: {e}")
            return None

    def is_team_mapped(self, api_football_id: int) -> bool:
        """
        Check if a team has a FootyStats mapping

        Args:
            api_football_id: Team ID from API-Football

        Returns:
            True if team is mapped to FootyStats
        """
        footystats_id = self.get_footystats_id(api_football_id)
        return footystats_id is not None

    def get_mapping_info(self, api_football_id: int) -> Optional[dict]:
        """
        Get complete mapping information for a team

        Args:
            api_football_id: Team ID from API-Football

        Returns:
            Dict with mapping details or None
        """
        try:
            with db_manager.get_session() as session:
                mapping = session.query(TeamIDMapping).filter_by(
                    api_football_id=api_football_id
                ).first()

                if not mapping:
                    return None

                return {
                    'api_football_id': mapping.api_football_id,
                    'footystats_id': mapping.footystats_id,
                    'team_name': mapping.team_name,
                    'league_id': mapping.league_id,
                    'confidence': mapping.confidence_score,
                    'is_verified': mapping.is_verified,
                    'last_updated': mapping.updated_at
                }

        except Exception as e:
            logger.error(f"Error getting mapping info: {e}")
            return None

    def get_all_mapped_teams(self, league_id: Optional[int] = None) -> list:
        """
        Get all teams that have FootyStats mappings

        Args:
            league_id: Optional league filter

        Returns:
            List of mapping dicts
        """
        try:
            with db_manager.get_session() as session:
                query = session.query(TeamIDMapping).filter(
                    TeamIDMapping.footystats_id.isnot(None)
                )

                if league_id:
                    query = query.filter_by(league_id=league_id)

                mappings = query.all()

                return [
                    {
                        'api_football_id': m.api_football_id,
                        'footystats_id': m.footystats_id,
                        'team_name': m.team_name,
                        'confidence': m.confidence_score
                    }
                    for m in mappings
                ]

        except Exception as e:
            logger.error(f"Error getting all mapped teams: {e}")
            return []
