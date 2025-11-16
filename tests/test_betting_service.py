import pytest
from datetime import datetime, timedelta
from src.services.betting_service import BettingService
from src.database.models import Race, RaceType


def test_can_place_bet_on_open_race():
    """Test that bets can be placed on open races"""
    race = Race(
        id=1,
        race_datetime=datetime.utcnow() + timedelta(hours=2),
        bet_close_datetime=datetime.utcnow() + timedelta(hours=1),
        status="betting_open"
    )
    
    can_bet, message = BettingService.can_place_bet(race)
    assert can_bet is True
    assert "Puedes apostar" in message


def test_cannot_place_bet_after_close():
    """Test that bets cannot be placed after close time"""
    race = Race(
        id=1,
        race_datetime=datetime.utcnow() + timedelta(hours=2),
        bet_close_datetime=datetime.utcnow() - timedelta(minutes=5),
        status="betting_open"
    )
    
    can_bet, message = BettingService.can_place_bet(race)
    assert can_bet is False
    assert "cerrado" in message.lower()


def test_cannot_place_bet_on_finished_race():
    """Test that bets cannot be placed on finished races"""
    race = Race(
        id=1,
        race_datetime=datetime.utcnow() - timedelta(hours=2),
        bet_close_datetime=datetime.utcnow() - timedelta(hours=3),
        status="finished"
    )
    
    can_bet, message = BettingService.can_place_bet(race)
    assert can_bet is False
    assert "finalizado" in message.lower()


def test_time_until_close():
    """Test time until close calculation"""
    race = Race(
        id=1,
        race_datetime=datetime.utcnow() + timedelta(hours=2),
        bet_close_datetime=datetime.utcnow() + timedelta(hours=1, minutes=30),
        status="betting_open"
    )
    
    time_str = BettingService.get_time_until_close(race)
    assert "h" in time_str or "m" in time_str
