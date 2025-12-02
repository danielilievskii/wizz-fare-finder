from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Flight
from app.db.connection import SessionLocal
from app.db.models import Airport, NearbyAirport

def save_flights(all_flights, db: Session):
    db.query(Flight).delete()

    for code, directions in all_flights.items():
        for direction, flights in directions.items():
            for f in flights:
                dep_dt = datetime.fromisoformat(f["departureDate"])
                db.add(Flight(
                    code=code,
                    direction=direction,
                    departure_station=f["departureStation"],
                    arrival_station=f["arrivalStation"],
                    discount_price=f["discountPrice"],
                    original_price=f["originalPrice"],
                    departure_date=dep_dt.strftime("%Y-%m-%d"),
                    departure_time=dep_dt.strftime("%H:%M")
                ))

    db.commit()


def get_flights(db: Session, departure_code: str, arrival_code: str):
    return (
        db.query(Flight)
        .filter(
            Flight.departure_station == departure_code,
            Flight.arrival_station == arrival_code
        )
        .all()
    )


def flights_to_dict(flights):
    """Convert SQLAlchemy Flight objects into dicts usable for matching."""
    return [
        {
            "departureStation": f.departure_station,
            "arrivalStation": f.arrival_station,
            "discountPrice": f.discount_price,
            "originalPrice": f.original_price,
            "departureDate": f"{f.departure_date}T{f.departure_time}"
        }
        for f in flights
    ]


def get_airport_codes():
    db: Session = SessionLocal()
    try:
        codes = db.query(Airport).all()
        return {airport.code: airport.name for airport in codes}
    finally:
        db.close()


def get_nearby_airports():
    db: Session = SessionLocal()
    try:
        rows = db.query(NearbyAirport).all()
        result = {}
        for row in rows:
            result.setdefault(row.airport_code, []).append(row.nearby_code)
        return result
    finally:
        db.close()
