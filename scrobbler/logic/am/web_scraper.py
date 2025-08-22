import json
import logging
from io import BytesIO
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from PIL import Image
from requests.exceptions import HTTPError, RequestException, Timeout

from config import Config

from ..song import Song

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrapes Apple Music web pages to fetch song metadata, duration, and artwork."""

    def __init__(self):
        self.session = requests.Session()

    def _build_search_url(self, title: str, artist: str, album: str) -> str:
        """Build a search URL for Apple Music using title of a song, artist name and album name."""

        search = f'{title} {artist} {album}'
        encoded_search = quote(search, safe='')

        return f'https://music.apple.com/us/search?term={encoded_search}'

    def fetch_data(self, url: str, is_image: bool = False) -> BeautifulSoup | Image.Image | None:
        """Fetch content from a URL.

        Args:
            url (str): URL to fetch.
            is_image (bool, optional): If True, fetch and return as a PIL Image. If False, return a BeautifulSoup object. Defaults to False.

        Returns:
            BeautifulSoup | Image.Image | None: Parsed HTML, image, or None if request failed.
        """

        try:
            response = self.session.get(url, timeout=10, stream=is_image)
            response.raise_for_status()
            if is_image:
                with Image.open(BytesIO(response.content)) as img:
                    img.load()
                    return img
            else:
                res = BeautifulSoup(response.text, 'html.parser')
                return res
        except (HTTPError, Timeout, RequestException):
            logger.warning("Couldn't fetch web page, URL: %s", url, exc_info=True)

    def update_metadata(self, song: Song) -> None:
        """Update song metadata by scraping Apple Music.

        Fetches:
        - Duration of the song (if not already provided by the app).
        - Album artwork (if GUI mode is not minimal).

        Args:
            song (Song): Song object to update.
        """

        song_search_url = self._build_search_url(song.metadata['title'], song.metadata['artist'], song.metadata['album'])
        search_soup = self.fetch_data(song_search_url)
        if not search_soup:
            return

        # Find first song in result from search
        song_tag = search_soup.find('div', {'class': 'track-lockup svelte-1tnc1ep is-link'})
        if not song_tag:
            return

        # Get URL of an album where the song is
        song_name_tag = song_tag.find('a', {'class': 'click-action svelte-c0t0j2'})
        if not song_name_tag:
            return

        album_url = song_name_tag.get('href')
        album_soup = self.fetch_data(album_url)
        if not album_soup:
            return

        script_tag = album_soup.find('script', type='application/json')
        if not script_tag:
            return

        try:
            json_album_data = json.loads(script_tag.text)[0]
        except (ValueError, IndexError, KeyError):
            logger.error('Apple Music changed structure of the script_tag.', exc_info=True)
            return

        # If no duration from AM app - then update duration
        if not song.metadata.get('is_app_duration', False):
            track_list = json_album_data.get('data', {}).get('sections', [{}, {}])[1].get('items', [])
            for track in track_list:
                if track.get('isProminent'):
                    duration = track.get('duration', 0) // 1000
                    if duration:
                        song.metadata['duration'] = duration

        if not Config.MINIMAL_GUI:
            # Get album's artwork
            artwork_data = (
                json_album_data.get('data', {}).get('sections', [{}])[0].get('items', [{}])[0].get('artwork', {}).get('dictionary', {})
            )
            if artwork_data and (artwork_url := artwork_data.get('url')):
                artwork_url = artwork_url.format(w=50, h=50, f='jpg')
                song.metadata['artwork'] = self.fetch_data(artwork_url, is_image=True)
