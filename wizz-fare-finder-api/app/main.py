import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.connection import Base, engine, SessionLocal
from app.db.models import Airport, NearbyAirport
from app.api.routes import router
from app.service.data_utils import save_flights
from app.service.flights_scraper import main as scrape_flights

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize scheduler
scheduler = AsyncIOScheduler()


async def scheduled_refresh_flights():
    """Background task to refresh flights at midnight"""
    db = SessionLocal()
    try:
        logger.info("Starting scheduled flight refresh")
        all_flights = await scrape_flights()
        save_flights(all_flights, db)
        logger.info("Flights refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing flights: {e}", exc_info=True)
    finally:
        db.close()


def load_airport_codes():
    """Load airport codes into database on startup"""
    db: Session = SessionLocal()
    try:
        if db.query(Airport).count() == 0:
            with open("app/core/data/airport_codes.json", "r", encoding="utf-8") as f:
                airport_codes = json.load(f)

            for code, airport in airport_codes.items():
                name, country = airport.split(" - ")
                db.add(Airport(code=code, name=name, country=country))
            db.commit()
            logger.info("Airport codes loaded into DB")
        else:
            logger.info("Airport codes already exist in DB")
    finally:
        db.close()


def load_nearby_airports():
    """Load nearby airports mapping into database on startup"""
    db: Session = SessionLocal()
    try:
        if db.query(NearbyAirport).count() == 0:
            with open("app/core/data/nearby_airports.json", "r", encoding="utf-8") as f:
                nearby_airports = json.load(f)

            for airport, nearby_list in nearby_airports.items():
                for nearby in nearby_list:
                    db.add(NearbyAirport(airport_code=airport, nearby_code=nearby))
            db.commit()
            logger.info("Nearby airports loaded into DB")
        else:
            logger.info("Nearby airports already exist in DB")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting application...")
    load_airport_codes()
    load_nearby_airports()

    logger.info("Running initial flight refresh...")
    await scheduled_refresh_flights()

    scheduler.add_job(
        scheduled_refresh_flights,
        'cron',
        hour=0,
        minute=0
    )
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)