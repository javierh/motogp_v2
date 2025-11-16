#!/usr/bin/env python3
"""
Script to manually sync MotoGP data from API
Usage: python sync_data.py [season]
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db
from src.services.data_sync_service import sync_all_data
from src.config import settings
from src.utils.logger import logger


async def main():
    """Main sync function"""
    # Get season from command line or use current
    season = int(sys.argv[1]) if len(sys.argv) > 1 else settings.current_season
    
    logger.info(f"🔄 Starting data sync for season {season}")
    print(f"\n🏍️  Syncing MotoGP data for season {season}...\n")
    
    with get_db() as db:
        results = await sync_all_data(db, season)
        
        print("\n📊 Sync Results:")
        print(f"   Calendar: {results['calendar']['count']} events - {results['calendar']['message']}")
        print(f"   Riders: {results['riders']['count']} riders - {results['riders']['message']}")
        
        if results["success"]:
            print("\n✅ Sync completed successfully!")
        else:
            print("\n❌ Sync completed with errors")
            if "message" in results:
                print(f"   Error: {results['message']}")


if __name__ == "__main__":
    asyncio.run(main())
