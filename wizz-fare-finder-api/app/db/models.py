from sqlalchemy import Column, Integer, String, Float
from app.db.connection import Base

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    direction = Column(String)  # outbound / return
    departure_station = Column(String)
    arrival_station = Column(String)
    discount_price = Column(Float)
    original_price = Column(Float)
    departure_date = Column(String)  # YYYY-MM-DD
    departure_time = Column(String)  # HH:MM

class Airport(Base):
    __tablename__ = "airports"

    code = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)

class NearbyAirport(Base):
    __tablename__ = "nearby_airports"

    airport_code = Column(String, primary_key=True)
    nearby_code = Column(String, primary_key=True)