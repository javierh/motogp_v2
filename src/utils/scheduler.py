"""
Scheduler for automated tasks
- Close betting when time expires
- Send notifications
- Update race data
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot

from src.config import settings
from src.database import get_db
from src.database.models import Race, Bet, Notification
from src.services import BettingService
from src.utils.logger import logger


class TaskScheduler:
    """Scheduler for automated tasks"""
    
    def __init__(self, telegram_bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = telegram_bot
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Check for betting close every minute
        self.scheduler.add_job(
            self.close_expired_bets,
            trigger=IntervalTrigger(minutes=1),
            id="close_bets",
            name="Close expired betting"
        )
        
        # Send bet closing warnings (15 minutes before)
        self.scheduler.add_job(
            self.send_closing_warnings,
            trigger=IntervalTrigger(minutes=5),
            id="closing_warnings",
            name="Send betting close warnings"
        )
        
        # Update race data every hour
        self.scheduler.add_job(
            self.update_race_data,
            trigger=IntervalTrigger(hours=1),
            id="update_races",
            name="Update race data"
        )
        
        logger.info("Scheduled jobs configured")
    
    async def close_expired_bets(self):
        """Close betting for races where time has expired"""
        try:
            with get_db() as db:
                races_to_close = BettingService.get_races_to_close(db)
                
                for race in races_to_close:
                    BettingService.close_betting(db, race.id)
                    
                    # Send notification to all users with bets
                    await self.notify_betting_closed(race)
                    
                if races_to_close:
                    logger.info(f"Closed betting for {len(races_to_close)} races")
                    
        except Exception as e:
            logger.error(f"Error closing bets: {e}", exc_info=True)
    
    async def send_closing_warnings(self):
        """Send warnings 15 minutes before betting closes"""
        try:
            with get_db() as db:
                now = datetime.utcnow()
                warning_time = now + timedelta(minutes=15)
                
                # Get races closing soon
                races = db.query(Race).filter(
                    Race.bet_close_datetime <= warning_time,
                    Race.bet_close_datetime > now,
                    Race.status == "betting_open"
                ).all()
                
                for race in races:
                    # Check if warning already sent
                    warning_sent = db.query(Notification).filter(
                        Notification.race_id == race.id,
                        Notification.notification_type == "bet_closing"
                    ).first()
                    
                    if not warning_sent:
                        await self.notify_betting_closing(race)
                        
                        # Log notification
                        notif = Notification(
                            notification_type="bet_closing",
                            race_id=race.id,
                            message=f"Betting closing warning for race {race.id}"
                        )
                        db.add(notif)
                        db.commit()
                        
        except Exception as e:
            logger.error(f"Error sending warnings: {e}", exc_info=True)
    
    async def notify_betting_closed(self, race: Race):
        """Send notification when betting closes"""
        try:
            with get_db() as db:
                # Get all bets for this race
                bets = BettingService.get_all_bets_for_race(db, race.id)
                
                if not bets:
                    return
                
                # Create summary message
                message = (
                    f"🔒 *Apuestas Cerradas*\n\n"
                    f"📅 {race.event.name}\n"
                    f"🏁 {race.category.name} - {race.race_type.name}\n\n"
                    f"📊 *Resumen de apuestas:*\n\n"
                )
                
                for bet in bets:
                    user = bet.user
                    name = user.first_name if user.first_name else user.username
                    
                    message += (
                        f"👤 {name}:\n"
                        f"🥇 #{bet.first_place.number} {bet.first_place.last_name}\n"
                        f"🥈 #{bet.second_place.number} {bet.second_place.last_name}\n"
                        f"🥉 #{bet.third_place.number} {bet.third_place.last_name}\n\n"
                    )
                
                message += "🏍️ ¡Buena suerte a todos!"
                
                # Send to all users who bet
                for bet in bets:
                    try:
                        await self.bot.send_message(
                            chat_id=bet.user.telegram_id,
                            text=message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Error sending to user {bet.user.telegram_id}: {e}")
                
                logger.info(f"Sent betting closed notification for race {race.id}")
                
        except Exception as e:
            logger.error(f"Error in notify_betting_closed: {e}", exc_info=True)
    
    async def notify_betting_closing(self, race: Race):
        """Send warning that betting is closing soon"""
        try:
            with get_db() as db:
                bets = BettingService.get_all_bets_for_race(db, race.id)
                
                message = (
                    f"⚠️ *¡Las apuestas cierran pronto!*\n\n"
                    f"📅 {race.event.name}\n"
                    f"🏁 {race.category.name} - {race.race_type.name}\n\n"
                    f"⏱️ Cierre en: {BettingService.get_time_until_close(race)}\n\n"
                    f"Usa /apostar o /editar para actualizar tu apuesta"
                )
                
                # Send to users with bets
                user_ids = set()
                if bets:
                    for bet in bets:
                        user_ids.add(bet.user.telegram_id)
                
                # TODO: Also send to all active users?
                
                for user_id in user_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Error sending to user {user_id}: {e}")
                
                logger.info(f"Sent closing warning for race {race.id}")
                
        except Exception as e:
            logger.error(f"Error in notify_betting_closing: {e}", exc_info=True)
    
    async def update_race_data(self):
        """Update race data from API"""
        try:
            # TODO: Implement API data fetching
            logger.debug("Race data update check")
        except Exception as e:
            logger.error(f"Error updating race data: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Task scheduler stopped")
