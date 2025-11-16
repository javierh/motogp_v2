"""
Admin scripts for database management
"""

import sys
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from src.database import get_db
from src.database.models import (
    Event, Race, Circuit, Category, RaceType, Rider, RiderSeason
)
from src.config import settings
from src.utils.logger import logger


def create_test_data():
    """Create test data for development"""
    logger.info("Creating test data...")
    
    with get_db() as db:
        # Get categories
        motogp = db.query(Category).filter(Category.code == "MOTOGP").first()
        moto2 = db.query(Category).filter(Category.code == "MOTO2").first()
        moto3 = db.query(Category).filter(Category.code == "MOTO3").first()
        
        # Get race types
        sprint = db.query(RaceType).filter(RaceType.code == "SPRINT").first()
        race = db.query(RaceType).filter(RaceType.code == "RACE").first()
        
        # Create test circuit
        circuit = Circuit(
            name="Circuit de Barcelona-Catalunya",
            country="Spain",
            location="Montmeló, Barcelona",
            external_id="CAT"
        )
        db.add(circuit)
        db.flush()
        
        # Create test event
        event_date = datetime.now().date() + timedelta(days=7)
        event = Event(
            season=settings.current_season,
            circuit_id=circuit.id,
            name="Catalunya GP",
            country="Spain",
            event_date=event_date,
            external_id="CAT_2024",
            is_current=True
        )
        db.add(event)
        db.flush()
        
        # Create test riders
        test_riders = [
            {"number": 93, "first_name": "Marc", "last_name": "Márquez", "country": "Spain"},
            {"number": 1, "first_name": "Francesco", "last_name": "Bagnaia", "country": "Italy"},
            {"number": 63, "first_name": "Pecco", "last_name": "Bagnaia", "country": "Italy"},
            {"number": 89, "first_name": "Jorge", "last_name": "Martín", "country": "Spain"},
            {"number": 12, "first_name": "Maverick", "last_name": "Viñales", "country": "Spain"},
            {"number": 20, "first_name": "Fabio", "last_name": "Quartararo", "country": "France"},
            {"number": 41, "first_name": "Aleix", "last_name": "Espargaró", "country": "Spain"},
            {"number": 23, "first_name": "Enea", "last_name": "Bastianini", "country": "Italy"},
            {"number": 43, "first_name": "Jack", "last_name": "Miller", "country": "Australia"},
            {"number": 33, "first_name": "Brad", "last_name": "Binder", "country": "South Africa"},
        ]
        
        riders = []
        for rider_data in test_riders:
            rider = Rider(**rider_data, external_id=str(rider_data["number"]))
            db.add(rider)
            riders.append(rider)
        
        db.flush()
        
        # Link riders to MotoGP category for current season
        for rider in riders:
            rider_season = RiderSeason(
                rider_id=rider.id,
                category_id=motogp.id,
                season=settings.current_season,
                team_name="Test Team",
                bike="Test Bike",
                is_active=True
            )
            db.add(rider_season)
        
        # Create test races
        race_datetime = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=14)
        bet_close_datetime = race_datetime - timedelta(minutes=settings.bet_close_minutes)
        
        # MotoGP Sprint
        motogp_sprint = Race(
            event_id=event.id,
            category_id=motogp.id,
            race_type_id=sprint.id,
            race_datetime=race_datetime - timedelta(days=1),
            bet_close_datetime=bet_close_datetime - timedelta(days=1),
            status="betting_open"
        )
        db.add(motogp_sprint)
        
        # MotoGP Race
        motogp_race = Race(
            event_id=event.id,
            category_id=motogp.id,
            race_type_id=race.id,
            race_datetime=race_datetime,
            bet_close_datetime=bet_close_datetime,
            status="betting_open"
        )
        db.add(motogp_race)
        
        # Moto2 Race
        moto2_race = Race(
            event_id=event.id,
            category_id=moto2.id,
            race_type_id=race.id,
            race_datetime=race_datetime - timedelta(hours=2),
            bet_close_datetime=bet_close_datetime - timedelta(hours=2),
            status="betting_open"
        )
        db.add(moto2_race)
        
        # Moto3 Race
        moto3_race = Race(
            event_id=event.id,
            category_id=moto3.id,
            race_type_id=race.id,
            race_datetime=race_datetime - timedelta(hours=3),
            bet_close_datetime=bet_close_datetime - timedelta(hours=3),
            status="betting_open"
        )
        db.add(moto3_race)
        
        db.commit()
        
        logger.info("Test data created successfully")
        logger.info(f"Created event: {event.name}")
        logger.info(f"Created {len(riders)} riders")
        logger.info("Created 4 races (MotoGP Sprint, MotoGP Race, Moto2 Race, Moto3 Race)")


def clear_test_data():
    """Clear all test data"""
    logger.warning("Clearing test data...")
    
    with get_db() as db:
        # Delete in order due to foreign keys
        db.query(Event).filter(Event.external_id.like("%_2024")).delete()
        db.query(Circuit).filter(Circuit.external_id == "CAT").delete()
        db.query(Rider).filter(Rider.external_id.in_([str(i) for i in range(1, 100)])).delete()
        
        db.commit()
        logger.info("Test data cleared")


def main():
    """Main admin script"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.admin_scripts <command>")
        print("Commands:")
        print("  create_test_data - Create test data for development")
        print("  clear_test_data  - Clear test data")
        return
    
    command = sys.argv[1]
    
    if command == "create_test_data":
        create_test_data()
    elif command == "clear_test_data":
        clear_test_data()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
