from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import Flight, Airport
from app.db.connection import get_db
from app.service.flights_scraper import main
from app.service.data_utils import get_nearby_airports, save_flights, get_flights, flights_to_dict, get_airport_codes
from app.service.matching_flights import find_matching_flights

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/refresh-flights")
async def refresh_flights(db: Session = Depends(get_db)):
    all_flights = await main()
    save_flights(all_flights, db)

    return {"status": "success", "message": "Flights refreshed and saved to DB"}


@router.get("/airports")
def get_all_airports(db: Session = Depends(get_db)):
    airports = db.query(Airport).all()
    return [{"code": airport.code, "name": airport.name, "country": airport.country} for airport in airports]


@router.get("/flights")
def get_all_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()

    # Convert to dicts without SQLAlchemy state info
    return [
        {
            "id": f.id,
            "code": f.code,
            "direction": f.direction,
            "departure_station": f.departure_station,
            "arrival_station": f.arrival_station,
            "discount_price": f.discount_price,
            "original_price": f.original_price,
            "departure_date": f.departure_date,
            "departure_time": f.departure_time,
        }
        for f in flights
    ]


@router.get("/search-flights")
def search_flights(
    destination_codes: str = Query(...),
    duration: int = Query(1),
    budget: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    all_matches = []

    airport_map = get_airport_codes()

    destination_codes = destination_codes.split(",")

    if "ALL" in destination_codes:
        destination_codes = list(airport_map.keys())

    for code in destination_codes:
        # Get outbound flights
        outbound_flights = get_flights(db, "SKP", code)
        outbound_list = flights_to_dict(outbound_flights)

        # Get return flights from this airport and its nearby airports
        return_flights = get_flights(db, code, "SKP")

        nearby_airports = get_nearby_airports()
        for nearby_code in nearby_airports.get(code, []):
            return_flights.extend(get_flights(db, nearby_code, "SKP"))

        return_list = flights_to_dict(return_flights)

        # Find matching round-trip flights
        matches = find_matching_flights(
            outbound_list,
            return_list,
            duration,
            budget,
            airport_map
        )

        all_matches.extend(matches)

    return all_matches