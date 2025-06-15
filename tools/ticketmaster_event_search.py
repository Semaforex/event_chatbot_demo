"""
ticketmaster_api.py

Handles interaction with the Ticketmaster Discovery API.
Provides a tool class to search for events based on parameters, compatible with BaseTool.
"""

import requests
from tools.base_tool import BaseTool
from config import TICKETMASTER_API_KEY
import json

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

class TicketmasterAPI(BaseTool):
    def __init__(self):
        with open("tools/descriptions/ticketmaster_event_search.json", "r") as file:
            self.tool_description = json.load(file)
    def get_description(self) -> str:
        return self.tool_description["function"]["description"]

    def run(self, params) -> str:
        """
        Run the Ticketmaster event search with the given parameters.
        Args:
            params (dict): Dictionary of search parameters.
        Returns:
            str: Summarized list of events or error message.
        """
        api_params = {
            "apikey": TICKETMASTER_API_KEY,
        }
        if "countryCode" in params and params["countryCode"]:
            api_params["countryCode"] = params["countryCode"]
        if "keyword" in params and params["keyword"]:
            api_params["keyword"] = params["keyword"]
        if "city" in params and params["city"]:
            api_params["city"] = params["city"]
        if "stateCode" in params and params["stateCode"]:
            api_params["stateCode"] = params["stateCode"]
        if "postalCode" in params and params["postalCode"]:
            api_params["postalCode"] = params["postalCode"]
        if "startDateTime" in params and params["startDateTime"]:
            api_params["startDateTime"] = params["startDateTime"]
        if "endDateTime" in params and params["endDateTime"]:
            api_params["endDateTime"] = params["endDateTime"]
        if "classificationName" in params and params["classificationName"]:
            api_params["classificationName"] = params["classificationName"]
        if "radius" in params and params["radius"]:
            api_params["radius"] = params["radius"]
        if "unit" in params and params["unit"]:
            api_params["unit"] = params["unit"]
        if "locale" in params and params["locale"]:
            api_params["locale"] = params["locale"]
        if "segmentId" in params and params["segmentId"]:
            api_params["segmentId"] = params["segmentId"]
        if "segmentName" in params and params["segmentName"]:
            api_params["segmentName"] = params["segmentName"]
        if "sort" in params and params["sort"]:
            api_params["sort"] = params["sort"]
        if "size" in params and params["size"]:
            api_params["size"] = params["size"]
        if "page" in params and params["page"]:
            api_params["page"] = params["page"]

        try:
            response = requests.get(BASE_URL, params=api_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            events = data.get("_embedded", {}).get("events", [])
            if not events:
                return "No events found for the given criteria."
            summary = []
            for event in events:
                name = event.get("name", "Unknown Event")
                url = event.get("url", "")
                dates = event.get("dates", {}).get("start", {})
                date_str = dates.get("localDate", "")
                time_str = dates.get("localTime", "")
                venue = ""
                venues = event.get("_embedded", {}).get("venues", [])
                if venues:
                    venue_name = venues[0].get("name", "")
                    city = venues[0].get("city", {}).get("name", "")
                    state = venues[0].get("state", {}).get("name", "")
                    venue = f"{venue_name}, {city}, {state}".strip(", ")
                summary.append(f"{name} at {venue} on {date_str} {time_str} - {url}")
            return "\n".join(summary)
        except requests.RequestException as e:
            return f"Error contacting Ticketmaster API: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
