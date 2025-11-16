import pytest
from src.services.scoring_service import ScoringService
from src.database.models import Bet, RaceResult, RaceType, Rider


def test_calculate_perfect_bet_score():
    """Test scoring with perfect prediction (all 3 exact + bonus)"""
    # Create mock race type with new scoring
    race_type = RaceType(
        points_exact_position=10,
        points_rider_only=5,
        points_perfect_podium=10
    )
    
    # Create mock riders
    rider1 = Rider(id=1)
    rider2 = Rider(id=2)
    rider3 = Rider(id=3)
    
    # Create mock bet (perfect prediction)
    bet = Bet(
        first_place_rider_id=1,
        second_place_rider_id=2,
        third_place_rider_id=3
    )
    
    # Create mock race results
    results = [
        RaceResult(rider_id=1, position=1, status="finished"),
        RaceResult(rider_id=2, position=2, status="finished"),
        RaceResult(rider_id=3, position=3, status="finished"),
    ]
    
    # Calculate score
    score = ScoringService.calculate_bet_score(bet, results, race_type)
    
    # 10 (1st exact) + 10 (2nd exact) + 10 (3rd exact) + 10 (bonus) = 40
    assert score["first"] == 10
    assert score["second"] == 10
    assert score["third"] == 10
    assert score["bonus"] == 10
    assert score["total"] == 40


def test_calculate_partial_bet_score():
    """Test scoring with partial correct prediction"""
    race_type = RaceType(
        points_exact_position=10,
        points_rider_only=5,
        points_perfect_podium=10
    )
    
    # Bet: 1st exact, 2nd wrong position (but in podium), 3rd not in podium
    bet = Bet(
        first_place_rider_id=1,
        second_place_rider_id=3,  # In podium but 3rd place
        third_place_rider_id=4   # Not in podium
    )
    
    results = [
        RaceResult(rider_id=1, position=1, status="finished"),
        RaceResult(rider_id=2, position=2, status="finished"),
        RaceResult(rider_id=3, position=3, status="finished"),
    ]
    
    score = ScoringService.calculate_bet_score(bet, results, race_type)
    
    # 10 (1st exact) + 5 (2nd in podium wrong pos) + 0 (3rd not in podium) = 15
    assert score["first"] == 10
    assert score["second"] == 5
    assert score["third"] == 0
    assert score["bonus"] == 0  # No perfect podium
    assert score["total"] == 15


def test_calculate_no_correct_bet_score():
    """Test scoring with no correct predictions"""
    race_type = RaceType(
        points_exact_position=10,
        points_rider_only=5,
        points_perfect_podium=10
    )
    
    bet = Bet(
        first_place_rider_id=4,
        second_place_rider_id=5,
        third_place_rider_id=6
    )
    
    results = [
        RaceResult(rider_id=1, position=1, status="finished"),
        RaceResult(rider_id=2, position=2, status="finished"),
        RaceResult(rider_id=3, position=3, status="finished"),
    ]
    
    score = ScoringService.calculate_bet_score(bet, results, race_type)
    
    assert score["first"] == 0
    assert score["second"] == 0
    assert score["third"] == 0
    assert score["bonus"] == 0
    assert score["total"] == 0


def test_calculate_all_riders_in_podium_wrong_positions():
    """Test: all 3 riders in podium but all in wrong positions"""
    race_type = RaceType(
        points_exact_position=10,
        points_rider_only=5,
        points_perfect_podium=10
    )
    
    # Predict 1-2-3, actual is 3-2-1 (reversed)
    bet = Bet(
        first_place_rider_id=3,
        second_place_rider_id=2,
        third_place_rider_id=1
    )
    
    results = [
        RaceResult(rider_id=1, position=1, status="finished"),
        RaceResult(rider_id=2, position=2, status="finished"),
        RaceResult(rider_id=3, position=3, status="finished"),
    ]
    
    score = ScoringService.calculate_bet_score(bet, results, race_type)
    
    # 5 (1st wrong pos) + 10 (2nd exact) + 5 (3rd wrong pos) = 20
    assert score["first"] == 5
    assert score["second"] == 10
    assert score["third"] == 5
    assert score["bonus"] == 0  # Not all exact
    assert score["total"] == 20
