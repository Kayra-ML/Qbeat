import asyncio
import collections

class GuildMusicState:
    def __init__(self, voice_channel_id):
        self.voice_channel_id = voice_channel_id
        self.assigned_bot = None
        self.voice_client = None
        self.queue = collections.deque()
        self.history = collections.deque()
        self.current_track = None
        self.repeat_mode = 0 # 0: Off, 1: Single, 2: Queue
        self.autoplay_enabled = True
        self.panel_message = None
        self.panel_channel_id = None
        self.is_transitioning = False
        self.lock = asyncio.Lock()
        self.last_activity = asyncio.get_event_loop().time()
        self.played_track_keys = set()
