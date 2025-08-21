import time
from math import ceil

from config import Config

from .am import AppScraper, WebScraper
from .lastfm import Lastfm
from .song import Song


def _handle_relistening(cur_time: int, song: Song, lastfm: Lastfm) -> None:
    """Handle a song that is being relistened to.

    If the song has already been played beyond its duration (and duration is from the Apple Music app), it will be scrobbled again.
    Resets the playtime and start timestamp, and updates the now playing status on Last.fm.

    Args:
        cur_time (int): Current time in seconds since epoch.
        song (Song): The Song object representing the current song.
        lastfm (Lastfm): Last.fm interface.
    """

    if song.is_rescrobbable():
        lastfm.scrobble_song(song)
        song.state['started_playing_timestamp'] = int(cur_time)
        song.state['playtime'] = 0
        lastfm.set_now_playing(song)


def _handle_no_metadata(song: Song, lastfm: Lastfm) -> None:
    """Handle the case when no metadata is detected from the Apple Music app.

    If the previous song is scrobbable, it is scrobbled. Then, the song's metadata and state are reset.

    Args:
        song (Song): The Song object representing the current song.
        lastfm (Lastfm): Last.fm interface.
    """

    if song.is_scrobbable():
        lastfm.scrobble_song(song)

    song.reset_metadata()
    song.reset_state()

    time.sleep(1)


def scrobble_at_exit(song: Song, lastfm: Lastfm) -> None:
    """Attempt to scrobble the current song when the application exits.

    Scrobbles the song if it is scrobbable or rescrobbable.

    Args:
        song (Song): The Song object representing the current song.
        lastfm (Lastfm): Last.fm interface.
    """

    if song.is_scrobbable() or song.is_rescrobbable():
        lastfm.scrobble_song(song)


def run_background(song: Song, lastfm: Lastfm) -> None:
    """Main background loop to monitor Apple Music and scrobble songs.

    This function continuously monitors the Apple Music app for currently playing music, updates song metadata,
    handles playtime tracking, scrobbles songs to Last.fm, and sets the now playing status.

    Logic:
        - Detects if a song is playing or paused.
        - Detects when a new song starts.
        - Updates song metadata from Apple Music app, Apple Music web, and Last.fm API.
        - Tracks the current playtime.
        - Scrobbles song.
        - Handles relistening to a song (rescrobbling if required).

    Args:
        song (Song): The Song object representing the current song.
        lastfm (Lastfm): Last.fm interface.
    """

    app_scraper = AppScraper()
    web_scraper = WebScraper()

    while True:
        # Get current song's metadata
        is_data = app_scraper.update_metadata(song)

        # No song in Apple Music window
        if not is_data:
            _handle_no_metadata(song, lastfm)
            continue

        # Try to set duration from the app
        if song.metadata.get('is_app_duration', False) and not song.state.get('is_app_duration', False) and song.is_same_song():
            song.state['duration'] = song.metadata['duration']
            song.state['is_app_duration'] = True

        cur_time = ceil(time.time())

        # Encountered new song
        if not song.is_same_song():
            song.increase_playtime(cur_time)

            # Try to scrobble song that was played before this one
            if song.is_scrobbable():
                lastfm.scrobble_song(song)

            song.reset_state()

            # If song is playing - get start of a listen, mark as started playing, mark as now playing on last.fm
            if song.metadata.get('playing', False):
                song.state['started_playing_timestamp'] = int(cur_time)
                song.state['last_time_played'] = cur_time
                song.state['started_playing'] = True
                song.state['playing'] = True

                lastfm.set_now_playing(song)

            # Get duration (if no duration from app) and artwork (if not minimal)
            if not song.metadata.get('is_app_duration', False) or not Config.MINIMAL_GUI:
                web_scraper.update_metadata(song)

            lastfm.update_metadata(song)
            song.state.update(song.metadata)

        # If we continue to listen to the same song
        elif song.metadata.get('playing', False):
            # If song was paused before that - mark as keep playing
            if not song.state.get('playing', False):
                lastfm.set_now_playing(song)
                song.state['playing'] = True

            # If it's a start of a listen - set timestamp and mark as started playing
            if not song.state.get('started_playing', False):
                song.state['started_playing_timestamp'] = int(cur_time)
                song.state['started_playing'] = True

            song.increase_playtime(cur_time)
            _handle_relistening(cur_time, song, lastfm)
            song.state['last_time_played'] = cur_time

        # If song is the same but paused (increase will happen if last time checked song was playing)
        else:
            song.increase_playtime(cur_time)
            song.state['last_time_played'] = None
            song.state['playing'] = False

        time.sleep(0.5)
