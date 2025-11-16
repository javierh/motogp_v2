"""
Scoring Service
Calculates points from race results
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.models import (
    Bet, BetScore, Race, RaceResult, RaceType,
    ChampionshipStanding, GlobalStanding, User, Category
)
from src.config import settings
from src.utils.logger import logger


class ScoringService:
    """Service for calculating and managing scores"""
    
    @staticmethod
    def calculate_bet_score(
        bet: Bet,
        race_results: List[RaceResult],
        race_type: RaceType
    ) -> Dict[str, int]:
        """
        Calculate points for a single bet based on race results
        
        New scoring system:
        - 10 points for exact match (correct rider + correct position)
        - 5 points for rider in podium but wrong position
        - +10 bonus for perfect podium (all 3 correct positions)
        
        Returns:
            Dictionary with points breakdown
        """
        if len(race_results) < 3:
            logger.warning(f"Insufficient race results for bet {bet.id}")
            return {"first": 0, "second": 0, "third": 0, "bonus": 0, "total": 0}
        
        # Get podium from results (sorted by position)
        podium = sorted(race_results[:3], key=lambda x: x.position)
        actual_first = podium[0].rider_id
        actual_second = podium[1].rider_id
        actual_third = podium[2].rider_id
        
        # Get all podium riders for checking "rider in podium but wrong position"
        podium_rider_ids = {actual_first, actual_second, actual_third}
        
        # Track exact matches for perfect podium bonus
        exact_matches = 0
        
        # Calculate points for first position prediction
        points_first = 0
        if bet.first_place_rider_id == actual_first:
            # Exact match: correct rider + correct position
            points_first = race_type.points_exact_position
            exact_matches += 1
        elif bet.first_place_rider_id in podium_rider_ids:
            # Rider is in podium but wrong position
            points_first = race_type.points_rider_only
        
        # Calculate points for second position prediction
        points_second = 0
        if bet.second_place_rider_id == actual_second:
            points_second = race_type.points_exact_position
            exact_matches += 1
        elif bet.second_place_rider_id in podium_rider_ids:
            points_second = race_type.points_rider_only
        
        # Calculate points for third position prediction
        points_third = 0
        if bet.third_place_rider_id == actual_third:
            points_third = race_type.points_exact_position
            exact_matches += 1
        elif bet.third_place_rider_id in podium_rider_ids:
            points_third = race_type.points_rider_only
        
        # Perfect podium bonus (all 3 exact matches)
        perfect_podium_bonus = 0
        if exact_matches == 3:
            perfect_podium_bonus = race_type.points_perfect_podium
            logger.info(f"🎉 Perfect podium for bet {bet.id}! Bonus: {perfect_podium_bonus} points")
        
        total = points_first + points_second + points_third + perfect_podium_bonus
        
        return {
            "first": points_first,
            "second": points_second,
            "third": points_third,
            "bonus": perfect_podium_bonus,
            "total": total
        }
    
    @staticmethod
    def process_race_results(db: Session, race_id: int) -> Tuple[bool, str]:
        """
        Process all bets for a race and calculate scores
        
        Returns:
            (success, message)
        """
        # Get race with relationships
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return False, "Carrera no encontrada"
        
        # Get race results (top 3 finishers)
        results = db.query(RaceResult).filter(
            and_(
                RaceResult.race_id == race_id,
                RaceResult.position <= 3,
                RaceResult.status == "finished"
            )
        ).order_by(RaceResult.position).all()
        
        if len(results) < 3:
            return False, f"Resultados incompletos (solo {len(results)} posiciones)"
        
        # Get all bets for this race
        bets = db.query(Bet).filter(Bet.race_id == race_id).all()
        
        if not bets:
            logger.info(f"No bets found for race {race_id}")
            return True, "Sin apuestas para procesar"
        
        # Calculate scores for each bet
        scores_created = 0
        for bet in bets:
            # Check if score already exists
            existing_score = db.query(BetScore).filter(
                BetScore.bet_id == bet.id
            ).first()
            
            if existing_score:
                logger.warning(f"Score already exists for bet {bet.id}")
                continue
            
            # Calculate points
            points = ScoringService.calculate_bet_score(bet, results, race.race_type)
            
            # Create bet score record
            bet_score = BetScore(
                bet_id=bet.id,
                race_id=race_id,
                user_id=bet.user_id,
                points_first=points["first"],
                points_second=points["second"],
                points_third=points["third"],
                perfect_podium_bonus=points["bonus"],
                total_points=points["total"]
            )
            
            db.add(bet_score)
            scores_created += 1
        
        db.commit()
        
        # Update championship standings
        ScoringService.update_championship_standings(db, race)
        
        logger.info(f"Processed {scores_created} bets for race {race_id}")
        return True, f"Procesadas {scores_created} apuestas"
    
    @staticmethod
    def update_championship_standings(db: Session, race: Race) -> None:
        """Update championship standings after a race"""
        season = race.event.season
        category_id = race.category_id
        
        # Get all scores for this race
        scores = db.query(BetScore).filter(BetScore.race_id == race.id).all()
        
        for score in scores:
            # Get or create championship standing
            standing = db.query(ChampionshipStanding).filter(
                and_(
                    ChampionshipStanding.season == season,
                    ChampionshipStanding.category_id == category_id,
                    ChampionshipStanding.user_id == score.user_id
                )
            ).first()
            
            if not standing:
                standing = ChampionshipStanding(
                    season=season,
                    category_id=category_id,
                    user_id=score.user_id,
                    total_points=0,
                    races_participated=0
                )
                db.add(standing)
            
            # Update standing
            standing.total_points += score.total_points
            standing.races_participated += 1
        
        db.commit()
        
        # Update global standings
        ScoringService.update_global_standings(db, season)
        
        logger.info(f"Updated championship standings for race {race.id}")
    
    @staticmethod
    def update_global_standings(db: Session, season: int) -> None:
        """Update global standings (all categories combined)"""
        # Get all users with standings
        category_standings = db.query(ChampionshipStanding).filter(
            ChampionshipStanding.season == season
        ).all()
        
        # Group by user
        user_points: Dict[int, Dict[str, int]] = {}
        
        for standing in category_standings:
            user_id = standing.user_id
            
            if user_id not in user_points:
                user_points[user_id] = {
                    "motogp": 0,
                    "moto2": 0,
                    "moto3": 0,
                    "total": 0,
                    "races": 0
                }
            
            # Get category code
            category = db.query(Category).filter(
                Category.id == standing.category_id
            ).first()
            
            if category:
                cat_key = category.code.lower()
                user_points[user_id][cat_key] = standing.total_points
                user_points[user_id]["total"] += standing.total_points
                user_points[user_id]["races"] += standing.races_participated
        
        # Update global standings
        for user_id, points in user_points.items():
            global_standing = db.query(GlobalStanding).filter(
                and_(
                    GlobalStanding.season == season,
                    GlobalStanding.user_id == user_id
                )
            ).first()
            
            if not global_standing:
                global_standing = GlobalStanding(
                    season=season,
                    user_id=user_id
                )
                db.add(global_standing)
            
            global_standing.motogp_points = points["motogp"]
            global_standing.moto2_points = points["moto2"]
            global_standing.moto3_points = points["moto3"]
            global_standing.total_points = points["total"]
            global_standing.races_participated = points["races"]
        
        db.commit()
        logger.info(f"Updated global standings for season {season}")
    
    @staticmethod
    def get_championship_standings(
        db: Session,
        season: int,
        category_id: Optional[int] = None,
        limit: int = 10
    ) -> List[ChampionshipStanding]:
        """Get championship standings"""
        query = db.query(ChampionshipStanding).filter(
            ChampionshipStanding.season == season
        )
        
        if category_id:
            query = query.filter(ChampionshipStanding.category_id == category_id)
        
        return query.order_by(
            ChampionshipStanding.total_points.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_global_standings(
        db: Session,
        season: int,
        limit: int = 10
    ) -> List[GlobalStanding]:
        """Get global standings"""
        return db.query(GlobalStanding).filter(
            GlobalStanding.season == season
        ).order_by(
            GlobalStanding.total_points.desc()
        ).limit(limit).all()
