import asyncio
import yt_dlp
from models.track import Track
from utils.logger import logger

class AudioService:
    def __init__(self):
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_opts)

    async def search_youtube(self, query: str, limit: int = 10):
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(f"ytsearch{limit}:{query}", download=False))
            return data.get('entries', [])
        except Exception as e:
            logger.error(f"ytsearch error: {e}")
            return []

    async def get_track_info(self, url: str, requester: str = None) -> Track:
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
                
            return Track(
                title=data.get('title', 'Unknown Title'),
                artist=data.get('uploader', 'Unknown Artist'),
                duration=data.get('duration', 0),
                webpage_url=data.get('webpage_url', url),
                audio_stream_url=data.get('url'),
                thumbnail_url=data.get('thumbnail'),
                requested_by=requester,
                source_type='youtube',
                youtube_id=data.get('id')
            )
        except Exception as e:
            logger.error(f"Error extracting info for {url}: {e}")
            return None

    async def resolve_stream_url(self, track: Track) -> str:
        if not track.webpage_url:
            return None
            
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(track.webpage_url, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            
            track.audio_stream_url = data.get('url')
            return track.audio_stream_url
        except Exception as e:
            logger.error(f"Error resolving stream URL for {track.webpage_url}: {e}")
            return None
