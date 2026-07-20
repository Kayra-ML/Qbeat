import os
import re
import asyncio
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY
from utils.logger import logger

class YouTubeService:
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.youtube = None
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                logger.error(f"YouTube API build failed: {e}")
        else:
            logger.warning("YOUTUBE_API_KEY not found. Using ytsearch fallback.")
            
        self.semaphore = asyncio.Semaphore(3)

    def _parse_duration(self, duration_str: str) -> float:
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        h, m, s = match.groups()
        h = int(h) if h else 0
        m = int(m) if m else 0
        s = int(s) if s else 0
        return h * 3600 + m * 60 + s

    def _score_and_select(self, target_title: str, target_artist: str, target_duration: float, videos: list):
        best_score = -999
        best_video = None
        
        target_title_lower = target_title.lower() if target_title else ""
        target_artist_lower = target_artist.lower() if target_artist else ""
        
        for video in videos:
            score = 0
            snippet = video['snippet']
            vid_title = snippet['title'].lower()
            vid_channel = snippet['channelTitle'].lower()
            
            duration_str = video.get('contentDetails', {}).get('duration', 'PT0S')
            vid_duration = self._parse_duration(duration_str)
            
            if target_title_lower in vid_title:
                score += 30
            
            if target_artist_lower in vid_title or target_artist_lower in vid_channel:
                score += 30
                
            if target_duration > 0 and vid_duration > 0:
                diff = abs(target_duration - vid_duration)
                if diff <= 10:
                    score += 20
                elif diff <= 20:
                    score += 10
                    
            if "official audio" in vid_title:
                score += 15
            if "topic" in vid_channel:
                score += 15
                
            original_query = f"{target_title_lower} {target_artist_lower}"
            penalties = ["live", "remix", "slowed", "reverb", "cover", "nightcore"]
            for p in penalties:
                if p in vid_title and p not in original_query:
                    score -= 50
                    
            if score > best_score:
                best_score = score
                best_video = video
                
        if best_score >= 30:
            return best_video
        return None

    async def search_and_match(self, title: str, artist: str, duration: float):
        search_query = f"{artist} - {title} official audio"
        
        if not self.youtube:
            return f"ytsearch:{search_query}"
            
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            
            def fetch_search():
                req = self.youtube.search().list(
                    q=search_query,
                    part="snippet",
                    type="video",
                    maxResults=5
                )
                return req.execute()
                
            try:
                search_response = await loop.run_in_executor(None, fetch_search)
                video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if item['id']['kind'] == 'youtube#video']
                
                if not video_ids:
                    return None
                    
                def fetch_videos():
                    req = self.youtube.videos().list(
                        part="snippet,contentDetails",
                        id=",".join(video_ids)
                    )
                    return req.execute()
                    
                videos_response = await loop.run_in_executor(None, fetch_videos)
                best_video = self._score_and_select(title, artist, duration, videos_response.get('items', []))
                
                if best_video:
                    return f"https://www.youtube.com/watch?v={best_video['id']}"
                
                logger.warning(f"Low confidence for: {search_query}, skipping.")
                return None
                
            except Exception as e:
                logger.error(f"YouTube search error: {e}")
                return f"ytsearch:{search_query}"
