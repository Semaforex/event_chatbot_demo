"""
event_categories.py

Provides a tool for querying Ticketmaster event categories, genres, and subgenres.
Follows the BaseTool interface for integration with agents.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from tools.base_tool import BaseTool

class EventCategoriesAPI(BaseTool):
    def __init__(self):
        """Initialize the event categories tool with data from types.json"""
        # Load tool description
        with open("tools/descriptions/ticketmaster_event_categories.json", "r") as file:
            self.tool_description = json.load(file)
            
        # Initialize data structures
        self.json_file = str(Path(__file__).parent.parent / "data" / "ticketmaster_event_types.json")
        self.segments = {}
        self.genres = {}
        self.subgenres = {}
        self.segment_map = {}  # Maps segment IDs to names
        self.genre_map = {}    # Maps genre IDs to names
        self.subgenre_map = {} # Maps subgenre IDs to names
        self._load_data()
    
    def get_description(self) -> str:
        """Get the tool description for the agent"""
        return self.tool_description["function"]["description"]

    def _load_data(self):
        """Load and parse the classification data from the JSON file"""
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
                
            # Extract classifications
            classifications = data.get('_embedded', {}).get('classifications', [])
            
            # Process each segment and its genres/subgenres
            for classification in classifications:
                segment = classification.get('segment', {})
                segment_id = segment.get('id')
                segment_name = segment.get('name')
                
                if segment_id and segment_name:
                    self.segment_map[segment_id] = segment_name
                    self.segments[segment_name] = {'id': segment_id, 'genres': {}}
                    
                    # Process genres
                    genres = segment.get('_embedded', {}).get('genres', [])
                    for genre in genres:
                        genre_id = genre.get('id')
                        genre_name = genre.get('name')
                        
                        if genre_id and genre_name:
                            self.genre_map[genre_id] = genre_name
                            self.genres[genre_name] = {'id': genre_id, 'segment': segment_name, 'subgenres': {}}
                            self.segments[segment_name]['genres'][genre_name] = genre_id
                            
                            # Process subgenres
                            subgenres = genre.get('_embedded', {}).get('subgenres', [])
                            for subgenre in subgenres:
                                subgenre_id = subgenre.get('id')
                                subgenre_name = subgenre.get('name')
                                
                                if subgenre_id and subgenre_name:
                                    self.subgenre_map[subgenre_id] = subgenre_name
                                    self.subgenres[subgenre_name] = {
                                        'id': subgenre_id,
                                        'genre': genre_name,
                                        'segment': segment_name
                                    }
                                    self.genres[genre_name]['subgenres'][subgenre_name] = subgenre_id
        except Exception as e:
            print(f"Error loading classification data: {e}")
    
    def run(self, params) -> str:
        """
        Execute the event categories query based on parameters
        
        Args:
            params (dict): Parameters for the query including action, segment, genre, etc.
            
        Returns:
            str: Formatted response with the requested category information
        """
        action = params.get('action')
        segment = params.get('segment')
        genre = params.get('genre')
        format_type = params.get('format', 'list')
        
        # Based on the action, call the appropriate method
        if action == 'list_segments':
            return self._format_segments(format_type)
        elif action == 'list_genres':
            return self._format_genres(segment, format_type)
        elif action == 'list_subgenres':
            return self._format_subgenres(genre, format_type)
        elif action == 'get_segment_id':
            return self._get_segment_id(segment)
        elif action == 'get_genre_id':
            return self._get_genre_id(genre)
        else:
            return f"Invalid action: {action}. Please use one of: list_segments, list_genres, list_subgenres, get_segment_id, or get_genre_id."

    def _format_segments(self, format_type: str) -> str:
        """Format the segments list based on the requested format"""
        if not self.segments:
            return "No segment data available."
            
        if format_type == 'list':
            return "Available segments: " + ", ".join(sorted(self.segments.keys()))
        else:  # detailed
            result = "Event Segments (Main Categories):\n\n"
            for name in sorted(self.segments.keys()):
                data = self.segments[name]
                result += f"- {name} (ID: {data['id']})\n"
            return result

    def _format_genres(self, segment: Optional[str], format_type: str) -> str:
        """Format the genres list based on the requested format and optional segment filter"""
        if segment and segment not in self.segments:
            return f"Segment '{segment}' not found. Available segments: {', '.join(sorted(self.segments.keys()))}"
            
        if segment:
            genres_to_show = {name: self.segments[segment]['genres'][name] 
                             for name in self.segments[segment]['genres']}
        else:
            genres_to_show = self.genres
            
        if not genres_to_show:
            return "No genre data available."
            
        if format_type == 'list':
            return f"Available genres{' for ' + segment if segment else ''}: " + ", ".join(sorted(genres_to_show.keys()))
        else:  # detailed
            result = f"Event Genres{' for ' + segment if segment else ''}:\n\n"
            for name in sorted(genres_to_show.keys()):
                if segment:
                    genre_id = genres_to_show[name]
                    result += f"- {name} (ID: {genre_id})\n"
                else:
                    data = self.genres[name]
                    result += f"- {name} (ID: {data['id']}, Segment: {data['segment']})\n"
            return result

    def _format_subgenres(self, genre: Optional[str], format_type: str) -> str:
        """Format the subgenres list based on the requested format and optional genre filter"""
        if genre and genre not in self.genres:
            return f"Genre '{genre}' not found. Available genres: {', '.join(sorted(self.genres.keys()))}"
            
        if genre:
            subgenres_to_show = {name: self.genres[genre]['subgenres'][name] 
                                for name in self.genres[genre]['subgenres']}
        else:
            subgenres_to_show = self.subgenres
            
        if not subgenres_to_show:
            return "No subgenre data available."
            
        if format_type == 'list':
            return f"Available subgenres{' for ' + genre if genre else ''}: " + ", ".join(sorted(subgenres_to_show.keys()))
        else:  # detailed
            result = f"Event Subgenres{' for ' + genre if genre else ''}:\n\n"
            for name in sorted(subgenres_to_show.keys()):
                if genre:
                    subgenre_id = subgenres_to_show[name]
                    result += f"- {name} (ID: {subgenre_id})\n"
                else:
                    data = self.subgenres[name]
                    result += f"- {name} (ID: {data['id']}, Genre: {data['genre']}, Segment: {data['segment']})\n"
            return result
            
    def _get_segment_id(self, segment: Optional[str]) -> str:
        """Get the ID for a given segment name"""
        if not segment:
            return "Please provide a segment name to get its ID."
            
        segment_id = self.segments.get(segment, {}).get('id')
        if segment_id:
            return f"ID for segment '{segment}': {segment_id}"
        else:
            return f"Segment '{segment}' not found. Available segments: {', '.join(sorted(self.segments.keys()))}"
            
    def _get_genre_id(self, genre: Optional[str]) -> str:
        """Get the ID for a given genre name"""
        if not genre:
            return "Please provide a genre name to get its ID."
            
        genre_id = self.genres.get(genre, {}).get('id')
        if genre_id:
            return f"ID for genre '{genre}': {genre_id}"
        else:
            return f"Genre '{genre}' not found. Available genres: {', '.join(sorted(self.genres.keys()))}"