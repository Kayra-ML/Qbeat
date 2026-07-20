import asyncio
from services.audio_service import AudioService
from models.track import Track
from utils.logger import logger

class RecommendationService:
    def __init__(self, audio_service: AudioService):
        self.audio_service = audio_service

    async def get_recommendation(self, state) -> Track:
        if not state.history:
            return None
            
        recent_tracks = list(state.history)[-5:]
        last_track = recent_tracks[-1]
        
        artists = [t.artist for t in recent_tracks if t.artist and t.artist != 'Unknown' and t.artist != 'Unknown Artist']
        if not artists:
            return None
            
        most_frequent_artist = max(set(artists), key=artists.count)
        
        target_artist = last_track.artist if (last_track.artist and last_track.artist != 'Unknown Artist') else most_frequent_artist
        
        search_query = f"{target_artist} official audio"
        
        entries = await self.audio_service.search_youtube(search_query, limit=15)
        
        played_keys = [t.canonical_key for t in list(state.history)[-20:]]
        played_titles = [t.title.lower() for t in list(state.history)[-20:] if t.title]
        
        for entry in entries:
            title = entry.get('title', '').lower()
            vid_id = entry.get('id')
            
            if f"yt:{vid_id}" in played_keys:
                continue
                
            if any(pt in title or title in pt for pt in played_titles):
                continue
                
            penalties = ["live", "cover", "slowed", "remix", "reverb", "nightcore"]
            if any(p in title for p in penalties):
                continue
                
            track = Track(
                title=entry.get('title', 'Unknown Title'),
                artist=entry.get('uploader', 'Unknown Artist'),
                duration=entry.get('duration', 0),
                webpage_url=entry.get('webpage_url', f"https://youtube.com/watch?v={vid_id}"),
                audio_stream_url=entry.get('url'),
                thumbnail_url=entry.get('thumbnail'),
                requested_by="Bot",
                source_type='youtube',
                youtube_id=vid_id,
                is_recommendation=True
            )
            return track
            
        return None
