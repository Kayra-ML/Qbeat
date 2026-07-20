import re

class InputParser:
    @staticmethod
    def parse_input(query: str):
        """
        Parses the input string and returns (type, query/id)
        Types:
        - spotify_playlist
        - spotify_track
        - spotify_album
        - spotify_artist
        - youtube_playlist
        - youtube_video
        - search_query
        """
        query = query.strip()
        
        if "spotify.com" in query:
            if "playlist" in query:
                return "spotify_playlist", query
            elif "track" in query:
                return "spotify_track", query
            elif "album" in query:
                return "spotify_album", query
            elif "artist" in query:
                return "spotify_artist", query
            
        if "youtube.com/playlist" in query or "&list=" in query:
            return "youtube_playlist", query
        elif "youtube.com/watch" in query or "youtu.be/" in query:
            return "youtube_video", query
            
        return "search_query", query
