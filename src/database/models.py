"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Numeric, ForeignKey, BigInteger, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class League(Base):
    """Football league"""
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teams = relationship("Team", back_populates="league")
    fixtures = relationship("Fixture", back_populates="league")

    def __repr__(self):
        return f"<League {self.name} ({self.country})>"


class Team(Base):
    """Football team"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    name = Column(String(100), nullable=False)
    logo_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    league = relationship("League", back_populates="teams")
    home_fixtures = relationship("Fixture", foreign_keys="[Fixture.home_team_id]", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="[Fixture.away_team_id]", back_populates="away_team")
    statistics = relationship("TeamStatistics", back_populates="team")

    def __repr__(self):
        return f"<Team {self.name}>"


class Fixture(Base):
    """Football match/fixture"""
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    kickoff_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="scheduled")  # scheduled, live, finished, postponed
    venue = Column(String(100))
    round = Column(String(50))

    # Season and week tracking (for calendar filtering and permanent storage)
    season = Column(Integer)  # e.g., 2025
    week = Column(Integer)  # Matchday/gameweek number (extracted from round)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Archival flag (for historical data management)
    is_archived = Column(Boolean, default=False)

    # Relationships
    league = relationship("League", back_populates="fixtures")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    odds = relationship("OddsHistory", back_populates="fixture")
    predictions = relationship("Prediction", back_populates="fixture")
    value_bets = relationship("ValueBet", back_populates="fixture")
    analysis_history = relationship("AnalysisHistory", back_populates="fixture")

    def __repr__(self):
        return f"<Fixture {self.id}: {self.home_team.name if self.home_team else 'TBD'} vs {self.away_team.name if self.away_team else 'TBD'}>"


class TeamStatistics(Base):
    """Team statistics for a season"""
    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    season = Column(Integer, nullable=False)

    # Overall stats
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_scored = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)

    # Home stats
    home_matches = Column(Integer, default=0)
    home_wins = Column(Integer, default=0)
    home_draws = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    home_goals_scored = Column(Integer, default=0)
    home_goals_conceded = Column(Integer, default=0)

    # Away stats
    away_matches = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_draws = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    away_goals_scored = Column(Integer, default=0)
    away_goals_conceded = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="statistics")

    def __repr__(self):
        return f"<TeamStatistics {self.team.name if self.team else 'TBD'} - {self.season}>"


class OddsHistory(Base):
    """Historical odds data"""
    __tablename__ = "odds_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    bookmaker = Column(String(50), nullable=False)
    market_type = Column(String(20), nullable=False)  # '1X2', 'Over/Under', etc.
    outcome = Column(String(20), nullable=False)  # 'Home', 'Draw', 'Away', etc.
    odds = Column(Numeric(5, 2), nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fixture = relationship("Fixture", back_populates="odds")

    def __repr__(self):
        return f"<OddsHistory {self.bookmaker} - {self.market_type} - {self.odds}>"


class Prediction(Base):
    """Generated predictions for fixtures"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))

    # Probabilities
    home_probability = Column(Numeric(5, 2), nullable=False)
    draw_probability = Column(Numeric(5, 2), nullable=False)
    away_probability = Column(Numeric(5, 2), nullable=False)

    # Expected goals
    expected_goals_home = Column(Numeric(4, 2))
    expected_goals_away = Column(Numeric(4, 2))

    # Metadata
    confidence_score = Column(Integer)  # 1-5
    analysis_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fixture = relationship("Fixture", back_populates="predictions")
    value_bets = relationship("ValueBet", back_populates="prediction")

    def __repr__(self):
        return f"<Prediction fixture={self.fixture_id} home={self.home_probability}%>"


class ValueBet(Base):
    """Detected value betting opportunities"""
    __tablename__ = "value_bets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"))
    prediction_id = Column(Integer, ForeignKey("predictions.id"))

    recommended_outcome = Column(String(20), nullable=False)  # 'Home', 'Draw', 'Away'
    calculated_probability = Column(Numeric(5, 2), nullable=False)
    bookmaker_odds = Column(Numeric(5, 2), nullable=False)
    edge = Column(Numeric(5, 2), nullable=False)  # Edge percentage
    expected_value = Column(Numeric(5, 2), nullable=False)
    suggested_stake = Column(Numeric(5, 2))  # % of bankroll

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fixture = relationship("Fixture", back_populates="value_bets")
    prediction = relationship("Prediction", back_populates="value_bets")
    notifications = relationship("NotificationLog", back_populates="value_bet")

    def __repr__(self):
        return f"<ValueBet {self.recommended_outcome} edge={self.edge}%>"


class NotificationLog(Base):
    """Log of sent notifications"""
    __tablename__ = "notifications_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value_bet_id = Column(Integer, ForeignKey("value_bets.id"))
    telegram_message_id = Column(BigInteger)
    status = Column(String(20), default="sent")  # sent, failed, retry
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    value_bet = relationship("ValueBet", back_populates="notifications")

    def __repr__(self):
        return f"<NotificationLog {self.status} at {self.sent_at}>"


class LeagueIDMapping(Base):
    """Mapping between API-Football and FootyStats league IDs"""
    __tablename__ = "league_id_mapping"

    id = Column(Integer, primary_key=True)
    api_football_id = Column(Integer, unique=True, nullable=False, index=True)
    footystats_id = Column(Integer, nullable=False)
    league_name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LeagueIDMapping {self.league_name} API:{self.api_football_id} FS:{self.footystats_id}>"


class TeamIDMapping(Base):
    """Mapping between API-Football and FootyStats team IDs"""
    __tablename__ = "team_id_mapping"

    id = Column(Integer, primary_key=True)
    api_football_id = Column(Integer, unique=True, nullable=False, index=True)
    footystats_id = Column(Integer, nullable=True)
    team_name = Column(String(100), nullable=False)
    league_id = Column(Integer, ForeignKey("league_id_mapping.api_football_id"), nullable=True)
    confidence_score = Column(Numeric(3, 2), default=1.0)  # 0.0-1.0 similarity score
    is_verified = Column(Boolean, default=False)  # Manual verification flag
    last_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TeamIDMapping {self.team_name} API:{self.api_football_id} FS:{self.footystats_id}>"


class AnalysisHistory(Base):
    """Historical analysis reports with PDF storage"""
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)

    # PDF storage
    pdf_url = Column(Text)  # Full URL for download
    pdf_cloudflare_key = Column(Text)  # R2 storage key

    # Confidence and ranking
    confidence_score = Column(Numeric(5, 2))  # 0-100 score for betting safety
    analysis_type = Column(String(50), default="complete")  # complete, quick, live

    # Snapshot data (for historical reference without joins)
    home_team_name = Column(String(100))
    away_team_name = Column(String(100))
    league_name = Column(String(100))
    kickoff_time = Column(DateTime)

    # Predictions snapshot
    home_probability = Column(Numeric(5, 2))
    draw_probability = Column(Numeric(5, 2))
    away_probability = Column(Numeric(5, 2))
    recommended_bet = Column(String(50))
    edge = Column(Numeric(5, 2))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fixture = relationship("Fixture", back_populates="analysis_history")

    def __repr__(self):
        return f"<AnalysisHistory fixture={self.fixture_id} confidence={self.confidence_score}>"
