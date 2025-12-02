import aiohttp
import asyncio
import requests

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from aiohttp.client_exceptions import ContentTypeError

from app.service.data_utils import get_airport_codes, get_nearby_airports
from app.core.config import WIZZ_AIR_BUILDNUMBER_URL


async def main():
    airport_codes = get_airport_codes()
    nearby_airports = get_nearby_airports()

    generated_dates = generate_two_month_ranges()
    all_flights_by_code = {}

    base_url = get_base_url()

    # Run all airports in parallel
    tasks = [
        process_airport(base_url, code, name, generated_dates, nearby_airports)
        for code, name in airport_codes.items()
    ]
    results = await asyncio.gather(*tasks)

    # Build dictionary
    for code, flights in results:
        all_flights_by_code[code] = flights

    return all_flights_by_code


def generate_two_month_ranges():
    # Use today's date automatically
    start_date = date.today()

    ranges = []
    current_start = start_date

    for _ in range(8):
        current_end = current_start + relativedelta(months=1)
        ranges.append((current_start.isoformat(), current_end.isoformat()))
        # Next start date = 1 day after the end date
        current_start = current_end + timedelta(days=1)

    return ranges


def process_flights(flight_list):
    processed = []

    for flight in flight_list:
        for dep_date in flight.get("departureDates", []):
            discount_price = flight.get("price").get("amount")
            original_price = flight.get("originalPrice").get("amount")

            if not discount_price:
                continue

            processed.append({
                "departureStation": flight.get("departureStation"),
                "arrivalStation": flight.get("arrivalStation"),
                "discountPrice": discount_price,
                "originalPrice": original_price,
                "departureDate": dep_date
            })
    return processed


async def fetch_flights(session, base_url, payload):
    async with session.post(base_url, json=payload) as resp:
        try:
            return await resp.json()
        except ContentTypeError:
            text = await resp.text()
            print(f"Non-JSON response {resp.status} → {text[:100]}...")
            return {}
        except Exception as e:
            print(f"Error fetching flights: {e}")
            return {}


async def process_airport(base_url, code, name, generated_dates, nearby_airports):
    all_outbound_flights = []
    all_return_flights = []

    async with aiohttp.ClientSession() as session:
        tasks = []

        for from_date, to_date in generated_dates:
            # Main request
            payload_main = {
                "adultCount": 1,
                "childCount": 0,
                "flightList": [
                    {"departureStation": "SKP", "arrivalStation": code, "from": from_date, "to": to_date},
                    {"departureStation": code, "arrivalStation": "SKP", "from": from_date, "to": to_date}
                ],
                "priceType": "regular",
                "infantCount": 0
            }
            tasks.append(fetch_flights(session, base_url, payload_main))

        # Run all requests concurrently
        results = await asyncio.gather(*tasks)

        # Process all results
        for data in results:
            outbound_flights = process_flights(data.get("outboundFlights", []))
            return_flights = process_flights(data.get("returnFlights", []))
            all_outbound_flights.extend(outbound_flights)
            all_return_flights.extend(return_flights)

    return code, {"outbound": all_outbound_flights, "return": all_return_flights}


def get_base_url():
    res = requests.get(WIZZ_AIR_BUILDNUMBER_URL)
    backend_url = res.text.split(" ")[1]
    return f'{backend_url}/Api/search/timetable'



