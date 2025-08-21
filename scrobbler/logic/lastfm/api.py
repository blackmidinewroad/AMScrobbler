import logging
import time
import webbrowser

import pylast

from config import Config
from scrobbler.filework import load_user_data, save_user_data
from scrobbler.utils import is_gif, make_circle

from ..am import WebScraper
from ..song import Song

logger = logging.getLogger(__name__)


class Lastfm:
    """Handles authentication, metadata retrieval, and scrobbling with the Last.fm API."""

    def __init__(self):
        self.network = pylast.LastFMNetwork(Config.API_KEY, Config.API_SECRET)
        self.username = None
        self.user_url = None
        self.user_obj = None
        self.avatar = None

    def is_valid_user_data(self, user_data: dict) -> bool:
        """Validate that loaded user data contains the required fields.

        Args:
            user_data (dict): Dictionary with stored Last.fm user data.

        Returns:
            bool: True if required keys ('session_key', 'username', 'user_url') are present, False otherwise.
        """

        required_keys = ('session_key', 'username', 'user_url')
        for required_key in required_keys:
            if required_key not in user_data:
                return False

        return True

    def auth_without_session_key(self) -> bool:
        """Authenticate the user via web login flow.

        Opens a browser for the user to log into Last.fm, then polls for up to 3 minutes to retrieve a session key.
        On success, saves user data locally.

        Returns:
            bool: True if authentication succeeded, False otherwise.
        """

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

        if not Config.MINIMAL_GUI:
            self.set_avatar()

        self.network.session_key = session_key

        return True

    def auth_with_session_key(self) -> bool:
        """Authenticate the user using a stored session key.

        Loads user data from file and initializes the Last.fm user object if valid.

        Returns:
            bool: True if authentication succeeded, False otherwise.
        """

        user_data = load_user_data()
        if not user_data or not self.is_valid_user_data(user_data):
            return False

        self.network.session_key = user_data['session_key']
        self.username = user_data['username']
        self.user_url = user_data['user_url']

        self.user_obj = self.network.get_user(self.username)

        if not Config.MINIMAL_GUI:
            self.set_avatar()

        return True

    def set_avatar(self) -> bool:
        """Fetch and process the user's Last.fm avatar.

        Downloads the avatar and converts non-GIF images into circular format.

        Returns:
            bool: True if avatar was successfully retrieved and processed, False otherwise.
        """

        url = None
        for _ in range(5):
            try:
                url = self.user_obj.get_image()
                break
            except pylast.NetworkError:
                logger.warning("Couldn't fetch user's avatar url due to pylast.NetworkError, username: %s", self.username)
                time.sleep(0.5)

        if not url:
            return False

        self.avatar = WebScraper().fetch_data(url, is_image=True)
        if not self.avatar:
            return False

        if not is_gif(self.avatar):
            self.avatar = make_circle(self.avatar)

        return True

    def set_now_playing(self, song: Song) -> None:
        """Update the 'now playing' status on Last.fm for the given song.

        Args:
            song (Song): Song object representing the song.
        """

        try:
            self.network.update_now_playing(
                title=song.metadata['title'],
                artist=song.metadata['artist'],
                album=song.metadata['album'],
                duration=song.metadata['duration'],
            )
        except pylast.NetworkError:
            logger.warning("Couldn't set 'now playing' for the song due to pylast.NetworkError, song metadata: %s", song.metadata)

    def scrobble_song(self, song: Song) -> None:
        """Scrobble given song.

        Args:
            song (Song): Song object representing the song.
        """
        for _ in range(5):
            try:
                self.network.scrobble(
                    title=song.state['title'],
                    artist=song.state['artist'],
                    album=song.state['album'],
                    timestamp=song.state['started_playing_timestamp'],
                )
                break
            except pylast.NetworkError:
                logger.warning("Couldn't scrobble the song due to pylast.NetworkError, song metadata: %s", song.state)
                time.sleep(0.5)

    def update_metadata(self, song: Song) -> None:
        """Update the song's metadata with corrections and duration from Last.fm.

        Attempts to correct the title and artist name, and fetch the track duration.
        Falls back to a default duration (120 seconds) if unavailable.

        Args:
            song (Song): Song object representing the song.
        """

        try:
            track = self.network.get_track(song.metadata['artist'], song.metadata['title'])
            artist = self.network.get_artist(song.metadata['artist'])

            corrected_track, corrected_artist = track.get_correction(), artist.get_correction()
            if corrected_track:
                song.metadata['title'] = corrected_track
            if corrected_artist:
                song.metadata['artist'] = corrected_artist

            duration = track.get_duration() // 1000
        except (pylast.WSError, pylast.NetworkError):
            duration = 0

        # If no duration neither from progress bar or AM web - set duration from last.fm
        if not song.metadata.get('duration', 0):
            if duration:
                song.metadata['duration'] = duration

            # If even on last.fm no duration set it as 2 minutes
            else:
                song.metadata['duration'] = 120
