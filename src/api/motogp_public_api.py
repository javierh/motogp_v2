"""
Real MotoGP Public API Client
Based on the public API used by motogp.com website
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
import aiohttp
from bs4 import BeautifulSoup

from src.config import settings
from src.utils.logger import logger


class MotoGPPublicAPIClient:
    """
    Client for MotoGP public API
    
    The MotoGP website uses a public API that can be accessed without authentication.
    Base URLs:
    - https://api.motogp.pulselive.com/motogp/v1/
    - https://resources.motogp.pulselive.com/
    """
    
    def __init__(self):
        self.base_url = "https://api.motogp.pulselive.com/motogp/v1"
        self.resources_url = "https://resources.motogp.pulselive.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Category mappings (API uses trademark symbols)
        self.category_map = {
            "MOTOGP": "MotoGP™",
            "MOTO2": "Moto2™",
            "MOTO3": "Moto3™"
        }
        
        # Category UUIDs (hardcoded for better performance)
        self.category_uuids = {
            "MOTOGP": "e8c110ad-64aa-4e8e-8a86-f2f152f6a942",
            "MOTO2": "549640b8-fd9c-4245-acfd-60e4bc38b25c",
            "MOTO3": "954f7e65-2ef2-4423-b949-4961cc603e45"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://www.motogp.com"
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def get_season_uuid(self, year: int) -> Optional[str]:
        """
        Get season UUID from year
        
        Args:
            year: Season year (e.g., 2024, 2025)
        
        Returns:
            Season UUID or None
        """
        try:
            data = await self._make_request("results/seasons")
            if data and isinstance(data, list):
                for season in data:
                    if season.get("year") == year:
                        return season.get("id")
            logger.error(f"Season {year} not found in API")
            return None
        except Exception as e:
            logger.error(f"Error getting season UUID: {e}")
            return None
    
    async def get_current_season(self) -> int:
        """Get current season year"""
        try:
            data = await self._make_request("results/seasons")
            if data and isinstance(data, list) and len(data) > 0:
                # Find current season
                for season in data:
                    if season.get("current", False):
                        return int(season.get("year", settings.current_season))
                # Fallback to first season
                return int(data[0].get("year", settings.current_season))
            return settings.current_season
        except Exception as e:
            logger.error(f"Error getting current season: {e}")
            return settings.current_season
    
    async def get_calendar(self, season: int) -> List[Dict[str, Any]]:
        """
        Get race calendar for a season
        
        Args:
            season: Year (e.g., 2024)
        
        Returns:
            List of events with details
        """
        try:
            logger.info(f"Fetching calendar for season {season}")
            # Get season UUID first
            season_uuid = await self.get_season_uuid(season)
            if not season_uuid:
                logger.error(f"Could not find UUID for season {season}")
                return []
            
            data = await self._make_request(f"results/events", params={"seasonUuid": season_uuid})
            
            events = []
            for event in data:
                event_info = {
                    "event_id": event.get("id"),
                    "name": event.get("name"),
                    "short_name": event.get("short_name"),
                    "country": event.get("country", {}).get("name"),
                    "circuit": event.get("circuit", {}).get("name"),
                    "circuit_id": event.get("circuit", {}).get("id"),
                    "location": event.get("circuit", {}).get("place"),
                    "date_start": event.get("date_start"),
                    "date_end": event.get("date_end"),
                    "test": event.get("test", False),
                    "sponsored_name": event.get("sponsored_name")
                }
                events.append(event_info)
            
            logger.info(f"Found {len(events)} events for season {season}")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching calendar: {e}")
            return []
    
    async def get_event_details(self, event_id: str, season: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an event
        
        Args:
            event_id: Event identifier
            season: Season year
        
        Returns:
            Event details including session schedule
        """
        try:
            # Get season UUID first
            season_uuid = await self.get_season_uuid(season)
            if not season_uuid:
                logger.error(f"Could not find UUID for season {season}")
                return None
            
            data = await self._make_request(f"results/event/{event_id}", params={"seasonUuid": season_uuid})
            return data
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            return None
    
    async def get_categories(self, season: int) -> List[Dict[str, Any]]:
        """
        Get racing categories for a season
        
        Returns:
            List of categories (MotoGP, Moto2, Moto3)
        """
        try:
            # Get season UUID first
            season_uuid = await self.get_season_uuid(season)
            if not season_uuid:
                logger.error(f"Could not find UUID for season {season}")
                return []
            
            data = await self._make_request(f"results/categories", params={"seasonUuid": season_uuid})
            return data if data else []
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []
    
    async def get_riders(self, season: int, category: str) -> List[Dict[str, Any]]:
        """
        Get riders for a specific category and season
        
        Args:
            season: Year
            category: Category UUID
        
        Returns:
            List of riders with details
        """
        try:
            logger.info(f"Fetching riders for {category} season {season}")
            # Get season UUID first
            season_uuid = await self.get_season_uuid(season)
            if not season_uuid:
                logger.error(f"Could not find UUID for season {season}")
                return []
            
            data = await self._make_request(
                f"results/riders",
                params={"seasonUuid": season_uuid, "categoryUuid": category}
            )
            
            riders = []
            for rider in data:
                rider_info = {
                    "rider_id": rider.get("id"),
                    "number": rider.get("current_career_step", {}).get("number"),
                    "first_name": rider.get("name"),
                    "last_name": rider.get("surname"),
                    "full_name": rider.get("full_name"),
                    "country": rider.get("country", {}).get("name"),
                    "country_iso": rider.get("country", {}).get("iso"),
                    "team": rider.get("current_career_step", {}).get("team"),
                    "bike": rider.get("current_career_step", {}).get("constructor", {}).get("name"),
                    "birth_date": rider.get("birth_date"),
                    "photo_url": rider.get("pictures", {}).get("profile", {}).get("main")
                }
                riders.append(rider_info)
            
            logger.info(f"Found {len(riders)} riders")
            return riders
            
        except Exception as e:
            logger.error(f"Error fetching riders: {e}")
            return []
    
    async def get_session_results(
        self,
        event_id: str,
        session_id: str,
        category: str,
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Get results for a practice/qualifying session
        
        Args:
            event_id: Event identifier
            session_id: Session identifier
            category: Category identifier
            season: Season year
        
        Returns:
            List of session results with lap times
        """
        try:
            logger.info(f"Fetching session results for event {event_id}, session {session_id}")
            data = await self._make_request(
                f"results/session/{session_id}/classification",
                params={
                    "eventUuid": event_id,
                    "categoryUuid": category
                }
            )
            
            results = []
            if data and "classification" in data:
                for entry in data["classification"]:
                    result = {
                        "position": entry.get("position"),
                        "rider_id": entry.get("rider", {}).get("id"),
                        "rider_name": entry.get("rider", {}).get("full_name"),
                        "rider_number": entry.get("rider", {}).get("number"),
                        "team": entry.get("team", {}).get("name"),
                        "constructor": entry.get("constructor", {}).get("name"),
                        "best_lap_time": entry.get("time"),
                        "gap": entry.get("gap", {}).get("first"),
                        "total_laps": entry.get("total_laps"),
                        "top_speed": entry.get("top_speed")
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching session results: {e}")
            return []
    
    async def get_race_results(
        self,
        event_id: str,
        session_id: str,
        category: str,
        season: int
    ) -> List[Dict[str, Any]]:
        """
        Get race results (same endpoint as session results)
        
        Args:
            event_id: Event identifier
            session_id: Session identifier (RAC for race, SPR for sprint)
            category: Category identifier
            season: Season year
        
        Returns:
            List of race results with final positions
        """
        # Race results use the same endpoint as session results
        return await self.get_session_results(event_id, session_id, category, season)
    
    async def get_championship_standings(
        self,
        season: int,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Get championship standings
        
        Args:
            season: Year
            category: Category identifier
        
        Returns:
            List of riders with championship points
        """
        try:
            logger.info(f"Fetching championship standings for {category} {season}")
            # Get season UUID first
            season_uuid = await self.get_season_uuid(season)
            if not season_uuid:
                logger.error(f"Could not find UUID for season {season}")
                return []
            
            data = await self._make_request(
                f"results/standings/riders",
                params={
                    "seasonUuid": season_uuid,
                    "categoryUuid": category
                }
            )
            
            standings = []
            if data and "standings" in data:
                for entry in data["standings"]:
                    standing = {
                        "position": entry.get("position"),
                        "rider_id": entry.get("rider", {}).get("id"),
                        "rider_name": entry.get("rider", {}).get("full_name"),
                        "rider_number": entry.get("rider", {}).get("number"),
                        "points": entry.get("points"),
                        "team": entry.get("team", {}).get("name"),
                        "constructor": entry.get("constructor", {}).get("name")
                    }
                    standings.append(standing)
            
            return standings
            
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return []
    
    async def get_category_id(self, category_code: str, season: int) -> Optional[str]:
        """
        Get category UUID from code (MOTOGP, MOTO2, MOTO3)
        
        Args:
            category_code: MOTOGP, MOTO2, or MOTO3
            season: Season year
        
        Returns:
            Category UUID or None
        """
        try:
            # First try hardcoded UUIDs (faster and more reliable)
            category_upper = category_code.upper()
            if category_upper in self.category_uuids:
                return self.category_uuids[category_upper]
            
            # Fallback to API lookup
            categories = await self.get_categories(season)
            category_name = self.category_map.get(category_upper)
            
            for cat in categories:
                if cat.get("name") == category_name:
                    return cat.get("id")
            
            logger.warning(f"Category {category_code} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting category ID: {e}")
            return None


# Factory function
def get_motogp_client() -> MotoGPPublicAPIClient:
    """Get MotoGP Public API client instance"""
    logger.info("Using MotoGP Public API client")
    return MotoGPPublicAPIClient()
