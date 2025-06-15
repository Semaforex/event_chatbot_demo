"""
ticketmaster_api.py

Handles interaction with the Ticketmaster Discovery API for event details.
Provides a tool class to fetch details for a specific event by ID, compatible with BaseTool.
"""

import requests
from tools.base_tool import BaseTool
import json
from env_config import get_ticketmaster_api_key

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events/{id}.json"

class TicketmasterEventDetailsAPI(BaseTool):
    def __init__(self):
        with open("tools/descriptions/event_details.json", "r") as file:
            self.tool_description = json.load(file)
    def get_description(self) -> str:
        return self.tool_description["function"]["description"]

    def run(self, params) -> str:
        """
        Run the Ticketmaster event details lookup with the given parameters.
        Args:
            params (dict): Dictionary with 'id' key for the event ID.
        Returns:
            str: Event details or error message.
        """
        event_id = params.get("id")
        if not event_id:
            return "Missing required parameter: id (event ID)."
        api_params = {
            "apikey": get_ticketmaster_api_key()
        }
        url = BASE_URL.format(id=event_id)
        try:
            response = requests.get(url, params=api_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Summarize key event details
            name = data.get("name", "Unknown Event")
            url = data.get("url", "")
            dates = data.get("dates", {}).get("start", {})
            date_str = dates.get("localDate", "")
            time_str = dates.get("localTime", "")
            venue = ""
            venues = data.get("_embedded", {}).get("venues", [])
            if venues:
                venue_name = venues[0].get("name", "")
                city = venues[0].get("city", {}).get("name", "")
                state = venues[0].get("state", {}).get("name", "")
                venue = f"{venue_name}, {city}, {state}".strip(", ")
            info = data.get("info", "")
            please_note = data.get("pleaseNote", "")
            price_ranges = data.get("priceRanges", [])
            price_info = ""
            if price_ranges:
                pr = price_ranges[0]
                min_price = pr.get("min")
                max_price = pr.get("max")
                currency = pr.get("currency")
                price_info = f"Price: {min_price} - {max_price} {currency}"
            summary = f"Event: {name}\nDate: {date_str} {time_str}\nVenue: {venue}\nURL: {url}"
            if price_info:
                summary += f"\n{price_info}"
            if info:
                summary += f"\nInfo: {info}"
            if please_note:
                summary += f"\nNote: {please_note}"
            return summary
        except requests.RequestException as e:
            return f"Error contacting Ticketmaster API: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
