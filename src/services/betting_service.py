"""
Betting Service
Handles bet creation, updates, and validations
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.models import Bet, Race, Rider, User
from src.config import settings
from src.utils.logger import logger


class BettingService:
    """Service for managing user bets"""
    
    @staticmethod
    def can_place_bet(race: Race) -> Tuple[bool, str]:
        """
        Check if bets can be placed for a race
        
        Returns:
            (can_bet, message)
        """
        now = datetime.utcnow()
        
        if race.status == "cancelled":
            return False, "Esta carrera ha sido cancelada"
        
        if race.status == "finished":
            return False, "Esta carrera ya ha finalizado"
        
        if now >= race.bet_close_datetime:
            return False, "El plazo para apostar ha cerrado"
        
        if race.status == "betting_closed":
            return False, "Las apuestas están cerradas para esta carrera"
        
        return True, "Puedes apostar"
    
    @staticmethod
    def get_time_until_close(race: Race) -> str:
        """Get human-readable time until betting closes"""
        now = datetime.utcnow()
        delta = race.bet_close_datetime - now
        
        if delta.total_seconds() < 0:
            return "Cerrado"
        
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    
    @staticmethod
    def create_bet(
        db: Session,
        user_id: int,
        race_id: int,
        first_rider_id: int,
        second_rider_id: int,
        third_rider_id: int
    ) -> Tuple[Optional[Bet], str]:
        """
        Create a new bet
        
        Returns:
            (bet, message)
        """
        # Validate race exists and is open for betting
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return None, "Carrera no encontrada"
        
        can_bet, message = BettingService.can_place_bet(race)
        if not can_bet:
            return None, message
        
        # Validate riders exist and are different
        if first_rider_id == second_rider_id or \
           first_rider_id == third_rider_id or \
           second_rider_id == third_rider_id:
            return None, "Los pilotos deben ser diferentes"
        
        riders = db.query(Rider).filter(
            Rider.id.in_([first_rider_id, second_rider_id, third_rider_id])
        ).all()
        
        if len(riders) != 3:
            return None, "Uno o más pilotos no son válidos"
        
        # Check if bet already exists
        existing_bet = db.query(Bet).filter(
            and_(Bet.user_id == user_id, Bet.race_id == race_id)
        ).first()
        
        if existing_bet:
            return None, "Ya tienes una apuesta para esta carrera. Usa /editar para modificarla"
        
        # Create bet
        bet = Bet(
            user_id=user_id,
            race_id=race_id,
            first_place_rider_id=first_rider_id,
            second_place_rider_id=second_rider_id,
            third_place_rider_id=third_rider_id
        )
        
        db.add(bet)
        db.commit()
        db.refresh(bet)
        
        logger.info(f"Bet created: User {user_id}, Race {race_id}")
        return bet, "Apuesta registrada correctamente"
    
    @staticmethod
    def update_bet(
        db: Session,
        user_id: int,
        race_id: int,
        first_rider_id: int,
        second_rider_id: int,
        third_rider_id: int
    ) -> Tuple[Optional[Bet], str]:
        """
        Update an existing bet
        
        Returns:
            (bet, message)
        """
        # Get existing bet
        bet = db.query(Bet).filter(
            and_(Bet.user_id == user_id, Bet.race_id == race_id)
        ).first()
        
        if not bet:
            return None, "No tienes apuesta para esta carrera"
        
        # Validate race is still open
        race = bet.race
        can_bet, message = BettingService.can_place_bet(race)
        if not can_bet:
            return None, message
        
        # Validate riders
        if first_rider_id == second_rider_id or \
           first_rider_id == third_rider_id or \
           second_rider_id == third_rider_id:
            return None, "Los pilotos deben ser diferentes"
        
        riders = db.query(Rider).filter(
            Rider.id.in_([first_rider_id, second_rider_id, third_rider_id])
        ).all()
        
        if len(riders) != 3:
            return None, "Uno o más pilotos no son válidos"
        
        # Update bet
        bet.first_place_rider_id = first_rider_id
        bet.second_place_rider_id = second_rider_id
        bet.third_place_rider_id = third_rider_id
        bet.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(bet)
        
        logger.info(f"Bet updated: User {user_id}, Race {race_id}")
        return bet, "Apuesta actualizada correctamente"
    
    @staticmethod
    def get_user_bet(db: Session, user_id: int, race_id: int) -> Optional[Bet]:
        """Get user's bet for a race"""
        return db.query(Bet).filter(
            and_(Bet.user_id == user_id, Bet.race_id == race_id)
        ).first()
    
    @staticmethod
    def get_all_bets_for_race(db: Session, race_id: int) -> List[Bet]:
        """Get all bets for a race"""
        return db.query(Bet).filter(Bet.race_id == race_id).all()
    
    @staticmethod
    def get_user_active_bets(db: Session, user_id: int) -> List[Bet]:
        """Get user's bets for upcoming/ongoing races"""
        return db.query(Bet).join(Race).filter(
            and_(
                Bet.user_id == user_id,
                Race.status.in_(["upcoming", "betting_open", "betting_closed", "in_progress"])
            )
        ).all()
    
    @staticmethod
    def close_betting(db: Session, race_id: int) -> bool:
        """Close betting for a race"""
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return False
        
        race.status = "betting_closed"
        db.commit()
        
        logger.info(f"Betting closed for race {race_id}")
        return True
    
    @staticmethod
    def get_races_to_close(db: Session) -> List[Race]:
        """Get races where betting should be closed"""
        now = datetime.utcnow()
        
        return db.query(Race).filter(
            and_(
                Race.bet_close_datetime <= now,
                Race.status.in_(["upcoming", "betting_open"])
            )
        ).all()
