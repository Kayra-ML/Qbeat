import urllib.parse

class Track:
    def __init__(self, title, artist, album=None, duration=0, webpage_url=None, 
                 audio_stream_url=None, thumbnail_url=None, requested_by=None, 
                 source_type=None, spotify_id=None, youtube_id=None, 
                 search_query=None, is_recommendation=False):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.webpage_url = webpage_url
        self.audio_stream_url = audio_stream_url
        self.thumbnail_url = thumbnail_url
        self.requested_by = requested_by
        self.source_type = source_type
        self.spotify_id = spotify_id
        self.youtube_id = youtube_id
        self.search_query = search_query
        self.is_recommendation = is_recommendation
        
        self.canonical_key = self._generate_canonical_key()
        
    def _generate_canonical_key(self):
        if self.youtube_id:
            return f"yt:{self.youtube_id}"
        elif self.spotify_id:
            return f"sp:{self.spotify_id}"
        
        norm_title = self.title.lower() if self.title else "unknown"
        norm_artist = self.artist.lower() if self.artist else "unknown"
        return f"str:{norm_title}-{norm_artist}"
