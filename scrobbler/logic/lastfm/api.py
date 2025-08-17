import logging
import sys
import time
import webbrowser
from pathlib import Path

import pylast

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from scrobbler.filework import load_user_data, save_user_data
from scrobbler.logic.am.web_scraper import WebScraper
from scrobbler.utils import is_gif, make_circle

logger = logging.getLogger(__name__)


class Lastfm:
    def __init__(self):
        self.network = pylast.LastFMNetwork(Config.API_KEY, Config.API_SECRET)
        self.username = None
        self.user_url = None
        self.user_obj = None
        self.avatar = None

    def is_valid_user_data(self, user_data: dict) -> bool:
        """Make sure all required values are present in the user data."""

        required_keys = ('session_key', 'username', 'user_url')
        for required_key in required_keys:
            if required_key not in user_data:
                return False

        return True

    def auth_without_session_key(self) -> bool:
        """Authenticate user via web. Return True if auth is successful, otherwise return False."""

        skg = pylast.SessionKeyGenerator(self.network)
        url = skg.get_web_auth_url()

        webbrowser.open(url)

        start = time.perf_counter()
        while True:
            try:
                # If user haven't logged in 3 minutes
                if (time.perf_counter() - start) >= 180:
                    return False

                session_key, self.username = skg.get_web_auth_session_key_username(url)
                self.user_obj = self.network.get_user(self.username)
                self.user_url = self.user_obj.get_url()
                break
            except pylast.WSError:
                time.sleep(1)

        user_data = {
            'session_key': session_key,
            'username': self.username,
            'user_url': self.user_url,
        }
        save_user_data(user_data)

        self.network.session_key = session_key

        return True

    def auth_with_session_key(self) -> bool:
        """Authenticate user with session key saved in json. Return True if auth is successful."""

        user_data = load_user_data()
        if not self.is_valid_user_data(user_data):
            return False

        self.network.session_key = user_data['session_key']
        self.username = user_data['username']
        self.user_url = user_data['user_url']

        self.user_obj = self.network.get_user(self.username)

        return True

    def set_avatar(self) -> bool:
        """Fetch user's last.fm avatar. Return True if successfully fetched avatar, otherwise return False."""

        for _ in range(5):
            try:
                url = self.user_obj.get_image()
                break
            except pylast.NetworkError:
                logger.warning("Couldn't fetch user's avatar url due to pylast.NetworkError, username: %s", self.username)
                continue

        if not url:
            return False

        self.avatar = WebScraper().fetch_data(url, is_image=True)
        if not self.avatar:
            return False

        if not is_gif(self.avatar):
            self.avatar = make_circle(self.avatar)

        return True

    def set_now_playing(self, metadata: dict) -> None:
        """Mark song as now_playing on last.fm."""

        try:
            self.network.update_now_playing(
                title=metadata['title'],
                artist=metadata['artist'],
                album=metadata['album'],
                duration=metadata['duration'],
            )
        except pylast.NetworkError:
            logger.warning("Couldn't set 'now playing' for the song due to pylast.NetworkError, song metadata: %s", metadata)
            pass

    def scrobble_song(self, metadata: dict) -> None:
        for _ in range(5):
            try:
                self.network.scrobble(
                    title=metadata['title'],
                    artist=metadata['artist'],
                    album=metadata['album'],
                    timestamp=metadata['timestamp'],
                )
                break
            except pylast.NetworkError:
                logger.warning("Couldn't scrobble the song due to pylast.NetworkError, song metadata: %s", metadata)
                continue

    def fetch_metadata(self, metadata: dict) -> dict:
        """Update song metadata with data from last.fm. Correct title and artist name if possible, get duration of a track."""

        try:
            track = self.network.get_track(metadata['artist'], metadata['title'])
            artist = self.network.get_artist(metadata['artist'])

            corrected_track, corrected_artist = track.get_correction(), artist.get_correction()
            metadata['artist'] = corrected_track if corrected_track else metadata['title']
            metadata['artist'] = corrected_artist if corrected_artist else metadata['artist']

            duration = track.get_duration() // 1000
        except (pylast.WSError, pylast.NetworkError):
            duration = 0

        # If no duration neither from progress bar or AM web - set duration from last.fm
        if not metadata['duration']:
            if duration:
                metadata['duration'] = duration

            # If even on last.fm no duration set it as 2 minutes
            else:
                metadata['duration'] = 120

        return metadata
