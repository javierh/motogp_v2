"""
Data Sync Service
Synchronizes MotoGP data from API to database
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.api import get_motogp_client
from src.database.models import (
    Event, Race, Circuit, Category, RaceType, Rider, RiderSeason,
    Session as DBSession, SessionType, SessionResult
)
from src.config import settings
from src.utils.logger import logger


class DataSyncService:
    """Service for syncing MotoGP data from API to database"""
    
    @staticmethod
    async def sync_calendar(db: Session, season: int) -> Tuple[int, str]:
        """
        Sync calendar events from API to database
        
        Returns:
            (events_synced, message)
        """
        try:
            async with get_motogp_client() as api:
                events_data = await api.get_calendar(season)
                
                if not events_data:
                    return 0, "No events found"
                
                events_synced = 0
                
                for event_data in events_data:
                    # Skip test events
                    if event_data.get("test", False):
                        continue
                    
                    # Get or create circuit
                    circuit = db.query(Circuit).filter(
                        Circuit.external_id == event_data["circuit_id"]
                    ).first()
                    
                    if not circuit:
                        circuit = Circuit(
                            name=event_data["circuit"],
                            country=event_data["country"],
                            location=event_data.get("location"),
                            external_id=event_data["circuit_id"]
                        )
                        db.add(circuit)
                        db.flush()
                    
                    # Get or create event
                    event = db.query(Event).filter(
                        Event.external_id == event_data["event_id"]
                    ).first()
                    
                    if not event:
                        event = Event(
                            season=season,
                            circuit_id=circuit.id,
                            name=event_data["name"],
                            country=event_data["country"],
                            event_date=datetime.fromisoformat(event_data["date_start"].replace("Z", "+00:00")).date(),
                            external_id=event_data["event_id"]
                        )
                        db.add(event)
                        events_synced += 1
                    else:
                        # Update existing event
                        event.name = event_data["name"]
                        event.country = event_data["country"]
                        event.event_date = datetime.fromisoformat(event_data["date_start"].replace("Z", "+00:00")).date()
                
                db.commit()
                logger.info(f"Synced {events_synced} events for season {season}")
                return events_synced, f"Synced {events_synced} events"
                
        except Exception as e:
            logger.error(f"Error syncing calendar: {e}", exc_info=True)
            db.rollback()
            return 0, f"Error: {str(e)}"
    
    @staticmethod
    async def sync_riders(db: Session, season: int) -> Tuple[int, str]:
        """
        Sync riders from API to database
        
        Returns:
            (riders_synced, message)
        """
        try:
            async with get_motogp_client() as api:
                # Get categories from DB
                categories = db.query(Category).filter(Category.is_active == True).all()
                
                total_riders_synced = 0
                
                for category in categories:
                    # Get category UUID from API
                    category_uuid = await api.get_category_id(category.code, season)
                    if not category_uuid:
                        logger.warning(f"Could not find UUID for category {category.code}")
                        continue
                    
                    # Get riders for this category
                    riders_data = await api.get_riders(season, category_uuid)
                    
                    for rider_data in riders_data:
                        # Skip if no number
                        if not rider_data.get("number"):
                            continue
                        
                        # Get or create rider
                        rider = db.query(Rider).filter(
                            Rider.external_id == rider_data["rider_id"]
                        ).first()
                        
                        if not rider:
                            rider = Rider(
                                first_name=rider_data["first_name"],
                                last_name=rider_data["last_name"],
                                number=rider_data["number"],
                                country=rider_data.get("country"),
                                external_id=rider_data["rider_id"]
                            )
                            db.add(rider)
                            db.flush()
                            total_riders_synced += 1
                        else:
                            # Update rider info
                            rider.first_name = rider_data["first_name"]
                            rider.last_name = rider_data["last_name"]
                            rider.number = rider_data["number"]
                            rider.country = rider_data.get("country")
                        
                        # Create or update rider season
                        rider_season = db.query(RiderSeason).filter(
                            and_(
                                RiderSeason.rider_id == rider.id,
                                RiderSeason.category_id == category.id,
                                RiderSeason.season == season
                            )
                        ).first()
                        
                        if not rider_season:
                            rider_season = RiderSeason(
                                rider_id=rider.id,
                                category_id=category.id,
                                season=season,
                                team_name=rider_data.get("team"),
                                bike=rider_data.get("bike"),
                                is_active=True
                            )
                            db.add(rider_season)
                        else:
                            rider_season.team_name = rider_data.get("team")
                            rider_season.bike = rider_data.get("bike")
                            rider_season.is_active = True
                
                db.commit()
                logger.info(f"Synced {total_riders_synced} riders for season {season}")
                return total_riders_synced, f"Synced {total_riders_synced} riders"
                
        except Exception as e:
            logger.error(f"Error syncing riders: {e}", exc_info=True)
            db.rollback()
            return 0, f"Error: {str(e)}"
    
    @staticmethod
    async def sync_event_races(db: Session, event_external_id: str, season: int) -> Tuple[int, str]:
        """
        Sync races for a specific event
        
        Args:
            event_external_id: External event ID from API
            season: Season year
        
        Returns:
            (races_synced, message)
        """
        try:
            # Get event from DB
            event = db.query(Event).filter(
                Event.external_id == event_external_id
            ).first()
            
            if not event:
                return 0, "Event not found in database"
            
            async with get_motogp_client() as api:
                # Get event details with session schedule
                event_data = await api.get_event_details(event_external_id, season)
                
                if not event_data:
                    return 0, "Could not fetch event details from API"
                
                # Get categories and race types
                categories = {cat.code: cat for cat in db.query(Category).all()}
                race_types = {rt.code: rt for rt in db.query(RaceType).all()}
                
                races_synced = 0
                
                # Process each category
                for cat_code, category in categories.items():
                    # Get category UUID
                    category_uuid = await api.get_category_id(cat_code, season)
                    if not category_uuid:
                        continue
                    
                    # Find race sessions in event data
                    # This requires parsing the event data structure
                    # TODO: Implement based on actual API response structure
                    
                    logger.info(f"Processed category {cat_code} for event {event.name}")
                
                db.commit()
                return races_synced, f"Synced {races_synced} races"
                
        except Exception as e:
            logger.error(f"Error syncing races: {e}", exc_info=True)
            db.rollback()
            return 0, f"Error: {str(e)}"
    
    @staticmethod
    async def update_race_results(
        db: Session,
        race_id: int
    ) -> Tuple[bool, str]:
        """
        Update race results from API
        
        Args:
            race_id: Database race ID
        
        Returns:
            (success, message)
        """
        try:
            from src.database.models import RaceResult
            
            # Get race from DB
            race = db.query(Race).filter(Race.id == race_id).first()
            if not race:
                return False, "Race not found"
            
            # Get event external ID
            event_external_id = race.event.external_id
            season = race.event.season
            
            async with get_motogp_client() as api:
                # Get category UUID
                category_uuid = await api.get_category_id(race.category.code, season)
                if not category_uuid:
                    return False, "Category not found in API"
                
                # Determine session ID based on race type
                # This is a simplified version - actual implementation needs proper session ID mapping
                session_id = "RAC" if race.race_type.code == "RACE" else "SPR"
                
                # Get results from API
                results_data = await api.get_race_results(
                    event_external_id,
                    session_id,
                    category_uuid,
                    season
                )
                
                if not results_data:
                    return False, "No results available from API"
                
                # Clear existing results
                db.query(RaceResult).filter(RaceResult.race_id == race_id).delete()
                
                # Insert new results
                for result_data in results_data:
                    # Find rider by external ID
                    rider = db.query(Rider).filter(
                        Rider.external_id == result_data["rider_id"]
                    ).first()
                    
                    if not rider:
                        logger.warning(f"Rider {result_data['rider_id']} not found in database")
                        continue
                    
                    result = RaceResult(
                        race_id=race_id,
                        rider_id=rider.id,
                        position=result_data["position"],
                        points=0,  # Official championship points, not our betting points
                        time_gap=result_data.get("gap"),
                        status="finished"
                    )
                    db.add(result)
                
                # Update race status
                race.status = "finished"
                
                db.commit()
                logger.info(f"Updated results for race {race_id}")
                return True, f"Updated {len(results_data)} results"
                
        except Exception as e:
            logger.error(f"Error updating race results: {e}", exc_info=True)
            db.rollback()
            return False, f"Error: {str(e)}"


async def sync_all_data(db: Session, season: int) -> Dict[str, Any]:
    """
    Sync all data for a season
    
    Returns:
        Dictionary with sync results
    """
    results = {
        "calendar": {"count": 0, "message": ""},
        "riders": {"count": 0, "message": ""},
        "success": False
    }
    
    try:
        # Sync calendar
        count, msg = await DataSyncService.sync_calendar(db, season)
        results["calendar"] = {"count": count, "message": msg}
        
        # Sync riders
        count, msg = await DataSyncService.sync_riders(db, season)
        results["riders"] = {"count": count, "message": msg}
        
        results["success"] = True
        
    except Exception as e:
        logger.error(f"Error in sync_all_data: {e}")
        results["message"] = str(e)
    
    return results
