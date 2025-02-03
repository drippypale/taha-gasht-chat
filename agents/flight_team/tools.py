from typing import Annotated, List
from langchain_core.tools import tool
from agents.flight_team.db import Database
from agents.flight_team import search_flights
import asyncio


@tool
def search_available_flights(
    origin: Annotated[
        str, "The departure city airport English name (e.g. 'Tehran', 'Mashhad')"
    ],
    destination: Annotated[
        str, "The arrival city airport English name (e.g., 'Tehran', 'Mashhad')"
    ],
    date: Annotated[str, "The departure date in YYYY-MM-DD format"],
    adult_count: Annotated[int, "Number of adult passengers"] = 1,
    child_count: Annotated[int, "Number of adult passengers"] = 0,
    infant_count: Annotated[int, "Number of adult passengers"] = 0,
    flight_class: Annotated[
        str, "Class of service (Economy, Business, or First)"
    ] = "Economy",
) -> List[dict]:
    """Search for available flights using the flight search API"""
    flights = asyncio.run(
        search_flights(
            flight_origin=origin,
            flight_dest=destination,
            departure_date=date,
            passengers_count=(adult_count, child_count, infant_count),
            flight_class=flight_class,
        )
    )
    return flights


@tool
def query_flight_database(
    query: Annotated[str, "SQL-like query string to search the flight database"],
) -> List[dict]:
    """Query the flight database for stored flight information.
    Here is the flights table schema:
    CREATE TABLE IF NOT EXISTS flights (
                    airline TEXT NOT NULL,
                    departure_datetime TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    origin_city TEXT NOT NULL,
                    origin_code TEXT NOT NULL,
                    dest_city TEXT NOT NULL,
                    dest_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    db = Database()
    return db.query_flights(query)
