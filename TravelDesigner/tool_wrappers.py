"""Typed wrappers for existing tool implementations.

Wraps functions from utils/web_apis.py and ItineraryAgent-master/agents/tool_funcs.py
with proper type hints and docstrings for auto JSON Schema generation.
"""

import os
import sys
import json
import requests
import dotenv

# Ensure project root is on the path and .env is loaded
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
dotenv.load_dotenv(os.path.join(root_dir, ".env"))

from utils import web_apis
from utils.config import SEARCH_NUM, SEARCH_REMAIN_NUM
from utils.utils import filter_search_results


def search_web(search_query: str, country: str = "us") -> str:
    """Search the web for information. Use only when other tools cannot provide the needed data.

    Args:
        search_query: The search query string.
        country: Country code for localized results (e.g. 'us', 'cn').
    """
    payload = json.dumps({"q": search_query, "num": SEARCH_NUM, "gl": country})
    response = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": os.getenv("SERPER_API_KEY"),
            "Content-Type": "application/json",
        },
        data=payload,
    )
    filtered_results, _ = filter_search_results(response.text, search_query)
    filtered_results = filtered_results[:SEARCH_REMAIN_NUM]
    return str([entry["content"] for entry in filtered_results])


def get_attractions(city: str, query: str = "must-visit attractions") -> str:
    """Retrieve major attractions in a city with ratings and ticket prices.

    Args:
        city: The city name to search attractions in.
        query: Search keywords to filter attractions (e.g. 'amusement parks', 'museums').
    """
    return web_apis.get_attractions(city=city, query=query)


def get_restaurants(city: str, query: str = "must-visit restaurants") -> str:
    """Retrieve restaurant recommendations for a city with ratings and average costs.

    Args:
        city: The city name to search restaurants in.
        query: Search keywords to filter restaurants (e.g. 'Japanese cuisine', 'seafood').
    """
    return web_apis.get_restaurants(city=city, query=query)


def get_accommodations(
    city: str,
    check_in_date: str,
    check_out_date: str,
    adults: int,
    min_price: int = 0,
    max_price: int = 999999999,
) -> str:
    """Retrieve hotel options for a city with prices and ratings.

    Args:
        city: The city name to search hotels in.
        check_in_date: Check-in date in YYYY-MM-DD format.
        check_out_date: Check-out date in YYYY-MM-DD format.
        adults: Number of adult guests.
        min_price: Minimum price per night in local currency.
        max_price: Maximum price per night in local currency.
    """
    return web_apis.get_accommodations(
        city=city,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        adults=adults,
        min_price=min_price,
        max_price=max_price,
    )


def get_flights(origin: str, destination: str, departure_date: str) -> str:
    """Retrieve flight information between two airports.

    Args:
        origin: Origin airport IATA code (e.g. ATL, LAX, JFK).
        destination: Destination airport IATA code (e.g. SFO, ORD).
        departure_date: Departure date in YYYY-MM-DD format.
    """
    return web_apis.get_flights(
        origin=origin, destination=destination, date=departure_date
    )


def get_distance_matrix(origin: str, destination: str, mode: str) -> str:
    """Get travel distance and duration between two locations.

    Args:
        origin: Starting location (address or place name).
        destination: Ending location (address or place name).
        mode: Travel mode - one of: driving, walking, bicycling, transit.
    """
    return web_apis.get_distance_matrix(
        origin=origin, destination=destination, mode=mode
    )
