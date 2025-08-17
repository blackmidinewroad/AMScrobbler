import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    API_KEY = os.getenv('API_KEY')
    API_SECRET = os.getenv('API_SECRET')

    AM_SCROBBLER_DATA_DIR = Path.home() / 'AMScrobbler'
    USER_DATA_FILE = AM_SCROBBLER_DATA_DIR / 'lastfm_user_data.json'
    LOG_FILE = AM_SCROBBLER_DATA_DIR / 'am_scrobbler.log'


def ensure_directories() -> None:
    """Ensure necessary directories exist"""

    Config.AM_SCROBBLER_DATA_DIR.mkdir(parents=True, exist_ok=True)
