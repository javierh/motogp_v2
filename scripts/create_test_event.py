#!/usr/bin/env python3
"""
Script para crear un evento de prueba con carreras
Útil para probar el sistema de apuestas sin esperar a un evento real
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import SessionLocal
from src.database.models import Event, Race, Circuit, Category, RaceType
from src.utils.logger import logger


def create_test_event():
    """Crear evento de prueba con carreras para las 3 categorías"""
    db = SessionLocal()
    
    try:
        # Obtener o crear circuito de prueba
        circuit = db.query(Circuit).filter(Circuit.name == "Test Circuit").first()
        if not circuit:
            circuit = Circuit(
                name="Test Circuit",
                country="Test Country",
                location="Test Location",
                external_id="test-circuit-001"
            )
            db.add(circuit)
            db.flush()
            logger.info(f"Created test circuit: {circuit.name}")
        else:
            logger.info(f"Using existing test circuit: {circuit.name}")
        
        # Crear evento de prueba para mañana
        tomorrow = datetime.now() + timedelta(days=1)
        event = db.query(Event).filter(Event.name == "TEST EVENT").first()
        
        if not event:
            event = Event(
                season=2025,
                circuit_id=circuit.id,
                name="TEST EVENT",
                country="Test Country",
                event_date=tomorrow.date(),
                external_id="test-event-001",
                is_current=True
            )
            db.add(event)
            db.flush()
            logger.info(f"Created test event: {event.name} on {event.event_date}")
        else:
            # Actualizar fecha para mañana
            event.event_date = tomorrow.date()
            event.is_current = True
            logger.info(f"Updated test event: {event.name} on {event.event_date}")
        
        # Obtener categorías y tipo de carrera
        categories = db.query(Category).filter(Category.is_active == True).all()
        race_type = db.query(RaceType).filter(RaceType.code == "RACE").first()
        
        if not race_type:
            logger.error("Race type 'RACE' not found in database")
            return
        
        races_created = 0
        
        # Crear una carrera para cada categoría
        for category in categories:
            # Verificar si ya existe una carrera para esta categoría en este evento
            existing_race = db.query(Race).filter(
                Race.event_id == event.id,
                Race.category_id == category.id,
                Race.race_type_id == race_type.id
            ).first()
            
            if not existing_race:
                # Crear horarios de carrera (carrera principal a las 14:00)
                race_datetime = datetime.combine(event.event_date, datetime.min.time())
                race_datetime = race_datetime.replace(hour=14, minute=0)  # Carrera a las 14:00
                
                # Cerrar apuestas 1 hora antes
                bet_close_datetime = race_datetime - timedelta(hours=1)
                
                race = Race(
                    event_id=event.id,
                    category_id=category.id,
                    race_type_id=race_type.id,
                    race_datetime=race_datetime,
                    bet_close_datetime=bet_close_datetime,
                    status="upcoming"
                )
                db.add(race)
                races_created += 1
                logger.info(f"Created race for {category.name} at {race_datetime}")
            else:
                # Actualizar fecha de la carrera existente
                race_datetime = datetime.combine(event.event_date, datetime.min.time())
                race_datetime = race_datetime.replace(hour=14, minute=0)
                bet_close_datetime = race_datetime - timedelta(hours=1)
                existing_race.race_datetime = race_datetime
                existing_race.bet_close_datetime = bet_close_datetime
                existing_race.status = "upcoming"
                logger.info(f"Updated race for {category.name} at {race_datetime}")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ TEST EVENT CREATED SUCCESSFULLY")
        print("="*60)
        print(f"\n📅 Event Details:")
        print(f"   Name: {event.name}")
        print(f"   Circuit: {circuit.name}")
        print(f"   Date: {event.event_date.strftime('%Y-%m-%d')} (Tomorrow)")
        print(f"   Season: {event.season}")
        
        print(f"\n🏁 Races Created:")
        races = db.query(Race).filter(Race.event_id == event.id).all()
        for race in races:
            print(f"   - {race.category.name}: {race.race_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"     Bets close: {race.bet_close_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"     Status: {race.status}")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Start the Telegram bot: docker-compose up -d")
        print(f"   2. Open bets: Use /abrir_apuestas command")
        print(f"   3. Place bets: Users can now bet on the podium")
        print(f"   4. Close bets: Use /cerrar_apuestas when ready")
        print(f"   5. Enter results: Use /resultado command")
        print(f"   6. Calculate scores: Scores will be calculated automatically")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error creating test event: {e}", exc_info=True)
        db.rollback()
        print(f"\n❌ Error creating test event: {e}\n")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Creating test event...")
    create_test_event()
