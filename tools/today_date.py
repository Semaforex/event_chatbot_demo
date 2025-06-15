"""
today_date.py

Provides a tool class to return today's date in ISO format, compatible with BaseTool.
"""

from tools.base_tool import BaseTool
import datetime
import json

class TodayDateTool(BaseTool):
    def __init__(self):
        with open("tools/descriptions/today_date.json", "r") as file:
            self.tool_description = json.load(file)
    def get_description(self) -> str:
        return self.tool_description["function"]["description"]

    def run(self, params) -> str:
        """
        Return today's date in ISO format (YYYY-MM-DD).
        Args:
            params (dict): Not used.
        Returns:
            str: Today's date as a string.
        """
        return datetime.date.today().isoformat()
