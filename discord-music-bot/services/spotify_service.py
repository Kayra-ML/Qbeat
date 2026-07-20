import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from utils.logger import logger

class SpotifyService:
    def __init__(self):
        self.client = None
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID, 
                    client_secret=SPOTIFY_CLIENT_SECRET
                )
                self.client = spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                logger.error(f"Spotify authentication failed: {e}")
        else:
            logger.warning("Spotify credentials not found. Spotify features will not work.")

    async def get_playlist_tracks(self, playlist_url: str):
        if not self.client:
            return []
            
        loop = asyncio.get_event_loop()
        try:
            playlist_id = playlist_url.split('/')[-1].split('?')[0]
            
            def fetch_playlist():
                results = self.client.playlist_items(playlist_id)
                tracks = results['items']
                while results['next']:
                    results = self.client.next(results)
                    tracks.extend(results['items'])
                return tracks
                
            raw_tracks = await loop.run_in_executor(None, fetch_playlist)
            
            parsed_tracks = []
            for item in raw_tracks:
                track = item.get('track')
                if not track:
                    continue
                title = track.get('name')
                artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
                duration = track.get('duration_ms', 0) / 1000.0
                spotify_id = track.get('id')
                
                parsed_tracks.append({
                    'title': title,
                    'artist': artist,
                    'duration': duration,
                    'spotify_id': spotify_id
                })
                
            return parsed_tracks
        except Exception as e:
            logger.error(f"Error fetching Spotify playlist: {e}")
            return []

    async def get_track(self, track_url: str):
        if not self.client:
            return None
            
        loop = asyncio.get_event_loop()
        try:
            track_id = track_url.split('/')[-1].split('?')[0]
            def fetch_track():
                return self.client.track(track_id)
                
            track = await loop.run_in_executor(None, fetch_track)
            if not track:
                return None
                
            title = track.get('name')
            artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
            duration = track.get('duration_ms', 0) / 1000.0
            spotify_id = track.get('id')
            
            return {
                'title': title,
                'artist': artist,
                'duration': duration,
                'spotify_id': spotify_id
            }
        except Exception as e:
            logger.error(f"Error fetching Spotify track: {e}")
            return None

    async def get_album_tracks(self, album_url: str):
        if not self.client:
            return []
            
        loop = asyncio.get_event_loop()
        try:
            album_id = album_url.split('/')[-1].split('?')[0]
            
            def fetch_album():
                results = self.client.album_tracks(album_id)
                tracks = results['items']
                while results['next']:
                    results = self.client.next(results)
                    tracks.extend(results['items'])
                return tracks
                
            raw_tracks = await loop.run_in_executor(None, fetch_album)
            
            parsed_tracks = []
            for track in raw_tracks:
                title = track.get('name')
                artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
                duration = track.get('duration_ms', 0) / 1000.0
                spotify_id = track.get('id')
                
                parsed_tracks.append({
                    'title': title,
                    'artist': artist,
                    'duration': duration,
                    'spotify_id': spotify_id
                })
                
            return parsed_tracks
        except Exception as e:
            logger.error(f"Error fetching Spotify album: {e}")
            return []

    async def get_artist_top_tracks(self, artist_url: str):
        if not self.client:
            return []
            
        loop = asyncio.get_event_loop()
        try:
            artist_id = artist_url.split('/')[-1].split('?')[0]
            
            def fetch_artist_tracks():
                return self.client.artist_top_tracks(artist_id)
                
            results = await loop.run_in_executor(None, fetch_artist_tracks)
            raw_tracks = results.get('tracks', [])
            
            parsed_tracks = []
            for track in raw_tracks:
                title = track.get('name')
                artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
                duration = track.get('duration_ms', 0) / 1000.0
                spotify_id = track.get('id')
                
                parsed_tracks.append({
                    'title': title,
                    'artist': artist,
                    'duration': duration,
                    'spotify_id': spotify_id
                })
                
            return parsed_tracks
        except Exception as e:
            logger.error(f"Error fetching Spotify artist: {e}")
            return []
