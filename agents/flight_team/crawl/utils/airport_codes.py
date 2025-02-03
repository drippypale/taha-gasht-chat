from typing import Optional
import pandas as pd
import os

from agents.flight_team.crawl.exceptions import InvalidAirportCodeError

current_dir = os.path.dirname(os.path.abspath(__file__))
airports_path = os.path.join(current_dir, "airports.csv")
AIRPORT_DF = pd.read_csv(airports_path)


def get_city_name(airport_code: str) -> str:
    """
    Get city name based on airport code

    Args:
        airport_code: Airport code

    Returns:
        City name
    """
    city = AIRPORT_DF[AIRPORT_DF["iata"] == airport_code]

    if city.empty:
        raise InvalidAirportCodeError(f"No city found for {airport_code}")

    return city["city"].values[0]


def get_airport_code(city_name: str, country_name: Optional[str] = None) -> str:
    """
    Get airport code based on city and country names

    Args:
        city_name: Name of the city
        country_name: Name of the country

    Returns:
        Airport code
    """
    if country_name:
        airport = AIRPORT_DF[
            (AIRPORT_DF["city"] == city_name) & (AIRPORT_DF["country"] == country_name)
        ]
    else:
        airport = AIRPORT_DF[AIRPORT_DF["city"] == city_name]

    if airport.empty:
        raise InvalidAirportCodeError(
            f"No airport found for {city_name}, {country_name}"
        )

    return airport["iata"].values.tolist()
