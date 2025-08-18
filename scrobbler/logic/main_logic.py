import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.logic.am.app_scraper import AppScraper
from scrobbler.logic.am.web_scraper import WebScraper
from scrobbler.logic.lastfm.api import Lastfm
from scrobbler.logic.song import Song


def handle_relistening(cur_time: float, song: Song, lastfm: Lastfm) -> None:
    """If listening to the same song several times in a row - scrobble and then reset timestamp and playtime, mark as now playing on last.fm."""

    if song.is_rescrobbable():
        lastfm.scrobble_song(song)
        song.state['started_playing_timestamp'] = int(cur_time)
        song.state['playtime'] = 0
        lastfm.set_now_playing(song)


def handle_no_metadata(song: Song, lastfm: Lastfm) -> None:
    """If no metadata from Apple Music app - try to scrobble last played song."""

    if song.is_scrobbable():
        lastfm.scrobble_song(song)

    song.reset_metadata()
    song.reset_state()

    time.sleep(1)


def scrobble_at_exit(song: Song, lastfm: Lastfm):
    """Scrobble song at exit if possible."""

    if song.is_scrobbable() or song.is_rescrobbable():
        lastfm.scrobble_song(song)


def run_background(minimalistic: bool, song: Song, lastfm: Lastfm) -> None:
    """Main function that executes background logic. Checks for music currently playing in Apple Music Windows app and scrobbles songs."""

    app_scraper = AppScraper()
    web_scraper = WebScraper()

    while True:
        # Get current song's metadata
        is_data = app_scraper.update_metadata(song)

        # No song in Apple Music window
        if not is_data:
            handle_no_metadata(song, lastfm)
            continue

        # Try to set duration from the app
        if song.metadata['is_app_duration'] and not song.state['is_app_duration'] and song.is_same_song():
            song.state['duration'] = song.metadata['duration']
            song.state['is_app_duration'] = True

        cur_time = time.time()

        # Encountered new song
        if not song.is_same_song():
            song.reset_state()

            # If new song is playing - get start of a listen, mark as started playing, mark as now playing on last.fm
            if song.metadata['playing']:
                song.state['started_playing_timestamp'] = int(cur_time)
                song.state['last_time_played'] = cur_time
                song.state['started_playing'] = True
                song.state['playing'] = True

                lastfm.set_now_playing(song)

            # Try to scrobble song that was played before this one
            if song.is_scrobbable():
                lastfm.scrobble_song(song)

            # Get duration (if no duration from app) and artwork (if not minimalistic)
            if not song.metadata['is_app_duration'] or not minimalistic:
                web_scraper.update_metadata_from_AM_web(song, include_artwork=not minimalistic)

            lastfm.update_metadata(song)
            song.state.update(song.metadata)

        # If we continue to listen to the same song
        elif song.metadata['playing']:
            # If song was paused before that - mark as keep playing
            if not song.state['playing']:
                lastfm.set_now_playing(song)
                song.state['playing'] = True

            # If it's a start of a listen - set timestamp and mark as started playing
            if not song.state['started_playing']:
                song.state['started_playing_timestamp'] = int(cur_time)
                song.state['started_playing'] = True

            song.increase_playtime(cur_time)
            handle_relistening(cur_time, song, lastfm)
            song.state['last_time_played'] = cur_time

        # If song is the same but paused (increase will happen if last time checked song was playing)
        else:
            song.increase_playtime(cur_time)
            song.state['last_time_played'] = None
            song.state['playing'] = False

        time.sleep(0.5)
