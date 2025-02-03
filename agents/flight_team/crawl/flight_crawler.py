from datetime import datetime
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError, Page
from typing import Optional, List, Dict
import json

from agents.flight_team.crawl.utils import date, airport_codes
from agents.flight_team.crawl.exceptions import (
    FlightSearchError,
    InvalidFlightClassError,
    InvalidPassengerCountError,
    InvalidAirportCodeError,
    DateConversionError,
)
from agents.flight_team.db.database import Database
from agents.flight_team.db.models import Flight

ALLOWED_FLIGHT_CLASSES = {"Economy", "Business", "First"}


async def search_flights(
    flight_origin: str,
    flight_dest: str,
    departure_date: str,
    passengers_count: tuple[int, int, int],  # (adults, childs, infants)
    flight_class: str,
    arrival_date: Optional[str] = None,
) -> None:
    print(
        f"Searching for flights...\n Origin: {flight_origin}\n Destination: {flight_dest}\n Departure Date: {departure_date}\n Passengers: {passengers_count}\n Class: {flight_class}\n Arrival Date: {arrival_date}"
    )
    """
    Search for flights on tahagasht.com using provided parameters and scrape flight information.

    Args:
        flight_origin (str): Departure city name (e.g., "Tehran").
        flight_dest (str): Destination city name (e.g., "Qeshm").
        departure_date (str): Date of departure in 'YYYY-MM-DD' format (Gregorian or Jalali).
        passengers_count (Tuple[int, int, int]): Number of passengers as (adults, childs, infants).
        flight_class (str): Class of flight ("Economy", "Business", "First").
        arrival_date (Optional[str]): Return flight date in 'YYYY-MM-DD' format for round trips.

    Returns:
        Optional[List[Dict]]: A list of dictionaries containing flight information, or None if failed.

    Raises:
        FlightSearchError: If any validation fails.
    """

    adults, childs, infants = passengers_count

    if flight_class.capitalize() not in ALLOWED_FLIGHT_CLASSES:
        raise InvalidFlightClassError(
            f"Invalid flight class '{flight_class}'. Must be one of {ALLOWED_FLIGHT_CLASSES}."
        )

    try:
        origin_codes = airport_codes.get_airport_code(flight_origin)
    except InvalidAirportCodeError as e:
        raise FlightSearchError(str(e))
    except Exception as e:
        raise FlightSearchError(
            f"Error retrieving origin airport codes: {str(e)}"
        ) from e

    try:
        dest_codes = airport_codes.get_airport_code(flight_dest)
    except InvalidAirportCodeError as e:
        raise FlightSearchError(str(e))
    except Exception as e:
        raise FlightSearchError(
            f"Error retrieving destination airport codes: {str(e)}"
        ) from e

    try:
        departure_date_greg = date.convert_to_gregorian(departure_date)
    except DateConversionError as e:
        raise FlightSearchError(str(e))

    if arrival_date:
        try:
            arrival_date_greg = date.convert_to_gregorian(arrival_date)
        except DateConversionError as e:
            raise FlightSearchError(str(e))
    else:
        arrival_date_greg = None

    if adults < 1:
        raise InvalidPassengerCountError("At least one adult must be present.")
    if adults + childs >= 10:
        raise InvalidPassengerCountError(
            "The total number of adults and children must be less than 10."
        )
    if infants > adults:
        raise InvalidPassengerCountError(
            "The number of infants cannot exceed the number of adults."
        )

    trip_type = "roundtrip" if arrival_date_greg else "oneway"

    all_flights = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        for origin_code in origin_codes:
            for dest_code in dest_codes:
                if origin_code == "IKA":
                    continue
                flight_json = {
                    "passengers": {
                        "adults": adults,
                        "childs": childs,
                        "infants": infants,
                    },
                    "other": {
                        "trip": trip_type,
                        "cabin": flight_class.capitalize(),
                    },
                    "routes": [
                        {
                            "from": {
                                "is_all": True,
                                "code": origin_code,
                                "title": flight_origin.capitalize(),
                                "country_code": "",
                                "country_name": "",
                                "city_name": flight_origin.capitalize(),
                                "latitude": 0,
                                "longitude": 0,
                                "city_fa": "",
                                "flightMultipleIndex": None,
                            },
                            "to": {
                                "is_all": True,
                                "code": dest_code,
                                "title": flight_dest.capitalize(),
                                "country_code": "",
                                "country_name": "",
                                "city_name": flight_dest.capitalize(),
                                "latitude": 0,
                                "longitude": 0,
                                "city_fa": "",
                                "flightMultipleIndex": None,
                            },
                            "dates": {
                                "departure": departure_date_greg,
                                "arrival": arrival_date_greg
                                if arrival_date_greg
                                else "",
                            },
                        }
                    ],
                }

                if trip_type == "oneway":
                    date_part = departure_date_greg
                else:
                    date_part = f"{departure_date_greg}&{arrival_date_greg}"

                url = f"https://www.tahagasht.com/flights/result/{origin_code}-{dest_code}/{date_part}/{trip_type}-{flight_class.capitalize()}-{adults}-{childs}-{infants}"

                page = await context.new_page()

                init_script = f"""
                    () => {{
                        localStorage.setItem("flightJson", `{json.dumps(flight_json)}`);
                    }}
                """
                await page.add_init_script(init_script)

                try:
                    await page.goto(url, timeout=60000)  # 60 seconds timeout
                    await page.evaluate(init_script)
                    await page.goto(url, timeout=60000)  # 60 seconds timeout

                    # Wait for the flight cards to load
                    try:
                        await page.wait_for_load_state("networkidle", timeout=60000)
                        await page.wait_for_selector(
                            "#flightResultContainer", timeout=60000
                        )  # 30 seconds timeout
                        await page.wait_for_selector(".flight-card", timeout=5000)
                    except TimeoutError:
                        print(f"No flights found for {origin_code} to {dest_code}.")
                        await page.close()
                        continue  # Skip to the next pair

                    flights = await scrape_flights(
                        page, origin_code, dest_code, departure_date_greg
                    )

                    all_flights.extend(flights)

                except Exception as e:
                    print(
                        f"An error occurred while searching flights from {origin_code} to {dest_code}: {e}"
                    )

                finally:
                    await page.close()

        await browser.close()

    # Insert flights into database
    if all_flights:
        db = Database()
        flights_to_insert = [Flight.from_dict(flight) for flight in all_flights]
        db.insert_flights(flights_to_insert)
    return all_flights


async def scrape_flights(
    page: Page, origin_code: str, dest_code: str, departure_date_greg: str
) -> List[Dict]:
    """
    Scrape flight information from the results page.

    Args:
        page (Page): Playwright page object.
        origin_code (str): Origin airport code.
        dest_code (str): Destination airport code.

    Returns:
        List[Dict]: A list of dictionaries containing flight details.
    """
    flights = []

    # Get all flight-card elements
    flight_cards = await page.query_selector_all(".flight-card")

    for index, card in enumerate(flight_cards, start=1):
        try:
            # Extract Airline Name
            airline = await card.eval_on_selector(
                ".flightInfo .col-3", "el => el.textContent.trim()"
            )

            # Extract Departure Time
            departure_time_str = await card.eval_on_selector(
                ".flightInfo .col-2 b", "el => el.textContent.trim()"
            )

            # Parse departure_time_str into time object
            try:
                departure_time = datetime.strptime(departure_time_str, "%H:%M").time()
            except ValueError:
                print(
                    f"Invalid departure time format '{departure_time_str}' for flight card {index}."
                )
                departure_time = None

            # Combine departure_date_greg and departure_time into datetime object
            if departure_time:
                departure_datetime = datetime.strptime(
                    f"{departure_date_greg} {departure_time_str}", "%Y-%m-%d %H:%M"
                )
            else:
                departure_datetime = None  # or handle accordingly

            # Click on "جزئیات پرواز" to reveal flight number
            details_button = await card.query_selector(
                "button:has-text('جزئیات پرواز')"
            )
            if details_button:
                await details_button.click()
                # Wait for the flight-details div to appear
                try:
                    await card.wait_for_selector(
                        ".flight-details", timeout=10000
                    )  # 10 seconds timeout
                except TimeoutError:
                    print(f"Flight details did not load for flight card {index}.")
                    flight_number = "N/A"
                else:
                    # Extract Flight Number
                    flight_details_el = await card.query_selector(".flight-details")
                    flight_number = await flight_details_el.eval_on_selector(
                        "span:has-text('شماره پرواز')",
                        "el => el.children[0].textContent.trim()",
                    )
            else:
                flight_number = "N/A"  # Default if button not found

            # Compile flight information
            flight_info = {
                "airline": airline,
                "departure_datetime": departure_datetime,
                "flight_number": flight_number,
                "origin_code": origin_code,
                "dest_code": dest_code,
            }

            flights.append(flight_info)

        except Exception as e:
            print(
                f"Failed to scrape flight card {index} from {origin_code} to {dest_code}: {e}"
            )
            continue

    return flights
