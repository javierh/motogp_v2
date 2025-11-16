"""
SQLAlchemy ORM Models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Date, Text,
    BigInteger, Enum, ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Telegram users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bets = relationship("Bet", back_populates="user")
    bet_scores = relationship("BetScore", back_populates="user")
    championship_standings = relationship("ChampionshipStanding", back_populates="user")
    global_standings = relationship("GlobalStanding", back_populates="user")


class Category(Base):
    """Racing categories (MotoGP, Moto2, Moto3)"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    races = relationship("Race", back_populates="category")
    rider_seasons = relationship("RiderSeason", back_populates="category")
    championship_standings = relationship("ChampionshipStanding", back_populates="category")


class Circuit(Base):
    """Racing circuits"""
    __tablename__ = "circuits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    location = Column(String(200))
    external_id = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    events = relationship("Event", back_populates="circuit")


class Event(Base):
    """Grand Prix events"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    external_id = Column(String(100), unique=True, index=True)
    is_current = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    circuit = relationship("Circuit", back_populates="events")
    races = relationship("Race", back_populates="event")


class RaceType(Base):
    """Race types (sprint, main race)"""
    __tablename__ = "race_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    points_exact_position = Column(Integer, nullable=False)  # 10 points
    points_rider_only = Column(Integer, nullable=False)  # 5 points
    points_perfect_podium = Column(Integer, nullable=False)  # 10 points bonus
    
    # Relationships
    races = relationship("Race", back_populates="race_type")


class Race(Base):
    """Specific races"""
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    race_type_id = Column(Integer, ForeignKey("race_types.id", ondelete="CASCADE"), nullable=False)
    race_datetime = Column(DateTime, nullable=False, index=True)
    bet_close_datetime = Column(DateTime, nullable=False, index=True)
    status = Column(
        Enum("upcoming", "betting_open", "betting_closed", "in_progress", "finished", "cancelled"),
        default="upcoming",
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("event_id", "category_id", "race_type_id", name="unique_race"),
    )
    
    # Relationships
    event = relationship("Event", back_populates="races")
    category = relationship("Category", back_populates="races")
    race_type = relationship("RaceType", back_populates="races")
    bets = relationship("Bet", back_populates="race")
    race_results = relationship("RaceResult", back_populates="race")
    sessions = relationship("Session", back_populates="race")
    bet_scores = relationship("BetScore", back_populates="race")


class Rider(Base):
    """Motorcycle riders"""
    __tablename__ = "riders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    number = Column(Integer, index=True)
    country = Column(String(100))
    external_id = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rider_seasons = relationship("RiderSeason", back_populates="rider")
    race_results = relationship("RaceResult", back_populates="rider")
    session_results = relationship("SessionResult", back_populates="rider")


class RiderSeason(Base):
    """Rider participation in categories per season"""
    __tablename__ = "rider_seasons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    season = Column(Integer, nullable=False, index=True)
    team_name = Column(String(200))
    bike = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    
    __table_args__ = (
        UniqueConstraint("rider_id", "category_id", "season", name="unique_rider_season"),
    )
    
    # Relationships
    rider = relationship("Rider", back_populates="rider_seasons")
    category = relationship("Category", back_populates="rider_seasons")


class Bet(Base):
    """User bets for races"""
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False, index=True)
    first_place_rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    second_place_rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    third_place_rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "race_id", name="unique_user_race_bet"),
        CheckConstraint(
            "first_place_rider_id != second_place_rider_id AND "
            "first_place_rider_id != third_place_rider_id AND "
            "second_place_rider_id != third_place_rider_id"
        ),
    )
    
    # Relationships
    user = relationship("User", back_populates="bets")
    race = relationship("Race", back_populates="bets")
    first_place = relationship("Rider", foreign_keys=[first_place_rider_id])
    second_place = relationship("Rider", foreign_keys=[second_place_rider_id])
    third_place = relationship("Rider", foreign_keys=[third_place_rider_id])
    bet_score = relationship("BetScore", back_populates="bet", uselist=False)


class RaceResult(Base):
    """Race results"""
    __tablename__ = "race_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False, index=True)
    rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    points = Column(Integer, default=0)
    time_gap = Column(String(50))
    status = Column(Enum("finished", "dnf", "dns", "dsq"), default="finished")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("race_id", "position", name="unique_race_position"),
    )
    
    # Relationships
    race = relationship("Race", back_populates="race_results")
    rider = relationship("Rider", back_populates="race_results")


class BetScore(Base):
    """Scores from user bets"""
    __tablename__ = "bet_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bet_id = Column(Integer, ForeignKey("bets.id", ondelete="CASCADE"), nullable=False, unique=True)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    points_first = Column(Integer, default=0)
    points_second = Column(Integer, default=0)
    points_third = Column(Integer, default=0)
    perfect_podium_bonus = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bet = relationship("Bet", back_populates="bet_score")
    race = relationship("Race", back_populates="bet_scores")
    user = relationship("User", back_populates="bet_scores")


class SessionType(Base):
    """Session types (FP, Q, etc.)"""
    __tablename__ = "session_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="session_type")


class Session(Base):
    """Practice and qualifying sessions"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type_id = Column(Integer, ForeignKey("session_types.id", ondelete="CASCADE"), nullable=False)
    session_datetime = Column(DateTime, nullable=False, index=True)
    status = Column(Enum("scheduled", "in_progress", "finished", "cancelled"), default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="sessions")
    session_type = relationship("SessionType", back_populates="sessions")
    session_results = relationship("SessionResult", back_populates="session")


class SessionResult(Base):
    """Session lap times and positions"""
    __tablename__ = "session_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, index=True)
    best_lap_time = Column(String(20))
    best_lap_number = Column(Integer)
    total_laps = Column(Integer)
    gap_to_first = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("session_id", "rider_id", name="unique_session_rider"),
    )
    
    # Relationships
    session = relationship("Session", back_populates="session_results")
    rider = relationship("Rider", back_populates="session_results")


class ChampionshipStanding(Base):
    """Championship standings by category"""
    __tablename__ = "championship_standings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_points = Column(Integer, default=0)
    races_participated = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("season", "category_id", "user_id", name="unique_season_category_user"),
        Index("idx_category_points", "category_id", "total_points"),
    )
    
    # Relationships
    category = relationship("Category", back_populates="championship_standings")
    user = relationship("User", back_populates="championship_standings")


class GlobalStanding(Base):
    """Global championship standings (all categories)"""
    __tablename__ = "global_standings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_points = Column(Integer, default=0, index=True)
    motogp_points = Column(Integer, default=0)
    moto2_points = Column(Integer, default=0)
    moto3_points = Column(Integer, default=0)
    races_participated = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("season", "user_id", name="unique_season_user"),
    )
    
    # Relationships
    user = relationship("User", back_populates="global_standings")


class Notification(Base):
    """Notifications log"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type = Column(
        Enum("bet_closing", "bet_closed", "race_result", "standings_update"),
        nullable=False,
        index=True
    )
    race_id = Column(Integer, ForeignKey("races.id", ondelete="SET NULL"))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
