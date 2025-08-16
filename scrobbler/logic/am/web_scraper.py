import json
import sys
from pathlib import Path
from urllib.parse import quote

import isodate
import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException, Timeout

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.utils import get_image_from_web


# Make URL for searching using title of a song, artist name and album name
def make_search_url(title, artist, album):
    search = f'{title} {artist} {album}'
    encoded_search = quote(search, safe='')
    return f'https://music.apple.com/us/search?term={encoded_search}'


# Get html of a search on Apple Music web
def get_soup(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except (HTTPError, Timeout, RequestException):
        return


# Fetch duration of a song from Apple Music web
def update_data_using_AM_web(metadata):
    song_search_url = make_search_url(metadata['title'], metadata['artist'], metadata['album'])
    search_soup = get_soup(song_search_url)
    if not search_soup:
        return

    # Find first song in result from search
    song_tag = search_soup.find('div', {'class': 'track-lockup svelte-nvj7sn is-link'})
    if not song_tag:
        return

    # Get URL of an album where the song is
    song_name_tag = song_tag.find('a', {'class': 'click-action svelte-yg0ebd'})
    album_url = song_name_tag.get('href')
    album_soup = get_soup(album_url)
    if not album_soup:
        return

    script_tag = album_soup.find('script', type='application/json')
    if not script_tag:
        return

    json_album_data = json.loads(script_tag.text)[0]

    # If no duration from AM app - then get duration from web: find duration in ISO format then convert it to seconds
    if not metadata['is_app_duration']:
        duration_iso = json_album_data['data']['seoData']['schemaContent']['audio']['duration']
        metadata['duration'] = isodate.parse_duration(duration_iso).seconds

    # # Get album's artwork
    # artwork_data = json_album_data['data']['sections'][0]['items'][0]['artwork']['dictionary']
    # # artwork_url = artwork_data['url'].format(w=artwork_data['width'], h=artwork_data['height'], f='jpg')
    # artwork_url = artwork_data['url'].format(w=50, h=50, f='jpg')
    # metadata['artwork'] = get_image_from_web(artwork_url)
