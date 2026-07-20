import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
WORKER_TOKENS_STR = os.getenv("WORKER_TOKENS", "")
WORKER_TOKENS = [t.strip() for t in WORKER_TOKENS_STR.split(",") if t.strip()]

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
IDLE_TIMEOUT_SECONDS = int(os.getenv("IDLE_TIMEOUT_SECONDS", 300))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 500))
MAX_PLAYLIST_SIZE = int(os.getenv("MAX_PLAYLIST_SIZE", 300))

TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")
