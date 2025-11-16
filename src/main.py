"""
Main application entry point
"""

import asyncio
import signal
import sys
from typing import Optional

from src.bot import NovaPorraBot
from src.database import init_db
from src.utils.logger import logger
from src.config import settings


class Application:
    """Main application"""
    
    def __init__(self):
        self.bot: Optional[NovaPorraBot] = None
        self.running = False
    
    async def start(self):
        """Start the application"""
        try:
            logger.info(f"Starting {settings.app_name}...")
            
            # Initialize database
            init_db()
            
            # Create and start bot
            self.bot = NovaPorraBot()
            self.running = True
            
            await self.bot.run()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await self.stop()
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            await self.stop()
            sys.exit(1)
    
    async def stop(self):
        """Stop the application"""
        if self.running:
            logger.info("Stopping application...")
            self.running = False
            # Cleanup tasks here if needed


def main():
    """Main entry point"""
    app = Application()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run application
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")


if __name__ == "__main__":
    main()
