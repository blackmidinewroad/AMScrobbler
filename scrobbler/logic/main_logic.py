import queue
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.logic.am.app_scraper import AppScraper
from scrobbler.logic.am.web_scraper import WebScraper
from scrobbler.logic.lastfm import api


# Check if we can scrobble track (song exists and playtime more than a half of runtime of a song)
def is_scrobbable(metadata):
    return metadata['id'] and metadata.get('playtime', 0) >= metadata['duration'] // 2


# Check if song is rescrobbable (playtime more than duration and duration of a song is from the AM app)
def is_re_scrobbable(metadata):
    return metadata['playtime'] > metadata['duration'] and metadata['is_app_duration']


# If last time checked song was playing - increase playtime by time now minus time then;
# Update last played time to now if currently song is playing and to False if song is paused
def increase_playtime(metadata, playing_now):
    time_now = time.time()
    if metadata['last_played']:
        metadata['playtime'] += time_now - metadata['last_played']
    metadata['last_played'] = time_now if playing_now else False


# If listening to the same song several times in a row - scrobble and then reset timestamp and playtime, mark as now playing on last.fm
def handle_relistening(metadata, network):
    if is_re_scrobbable(metadata):
        api.scrobble_song(metadata, network)
        metadata['timestamp'], metadata['playtime'] = int(time.time()), 0
        api.set_now_playing(metadata, network)


# Add current song's info to queue so it can be displayed
def update_queue(metadata_queue: queue.Queue, prev_metadata):
    if not metadata_queue.full():
        metadata_queue.put(prev_metadata)


# If no metadata from Apple Music app - try to scrobble last song and empty prev_metadata
def handle_no_metadata(prev_metadata, metadata_queue, network):
    update_queue(metadata_queue, False)

    if is_scrobbable(prev_metadata):
        api.scrobble_song(prev_metadata, network)

    prev_metadata.clear()
    prev_metadata['id'] = ''

    time.sleep(1)


# Scrobble song at exit if possible
def scrobble_at_exit():
    try:
        if is_scrobbable(prev_metadata):
            api.scrobble_song(prev_metadata, exit_network)

    # Closed before background started running, so there are no prev_metadata and network
    except NameError:
        pass


# Main function that checks for music currently playing in Apple Music Windows app, scrobbles songs
def run_background(network, metadata_queue: queue.Queue, minimalistic):
    # Global for scrobble at exit
    global prev_metadata, exit_network
    exit_network = network
    prev_metadata = {'id': ''}

    app_scraper = AppScraper()
    web_scraper = WebScraper()

    while True:
        # Get current song's metadata
        cur_metadata = app_scraper.get_data_from_AM_app(prev_id=prev_metadata['id'], is_app_duration=prev_metadata.get('is_app_duration'))

        # No song in Apple Music window
        if not cur_metadata or cur_metadata == 'X':
            handle_no_metadata(prev_metadata, metadata_queue, network)
            continue

        # Try to set duration from the app
        if cur_metadata['is_app_duration'] and not prev_metadata.get('is_app_duration') and cur_metadata['same_song']:
            prev_metadata['duration'] = cur_metadata['duration']
            prev_metadata['is_app_duration'] = True

        # Encountered new song
        if not cur_metadata['same_song']:
            cur_time = time.time()

            # Scrobble last song if possible
            if is_scrobbable(prev_metadata):
                api.scrobble_song(prev_metadata, network)

            # Get duration (if no duration from app) and artwork (if not minimalistic)
            if not cur_metadata['is_app_duration'] or not minimalistic:
                web_scraper.update_metadata_from_AM_web(cur_metadata, include_artwork=not minimalistic)

            prev_metadata = api.get_more_metadata(cur_metadata, network)

            # If new song is playing - get start of a listen, mark as started playing, mark as now_playing on last.fm
            if cur_metadata['playing']:
                prev_metadata['timestamp'], prev_metadata['last_played'] = int(cur_time), cur_time
                started_playing = True
                api.set_now_playing(prev_metadata, network)

            # If new song is paused - mark as not started playing
            else:
                prev_metadata['last_played'] = False
                started_playing = False

            # Update UI with new song
            update_queue(metadata_queue, prev_metadata if prev_metadata['playing'] else False)

        # If we continue to listen to the same song
        elif cur_metadata['playing']:
            # Update UI if song was on pause before
            if not prev_metadata['playing']:
                update_queue(metadata_queue, prev_metadata)

            # If song was paused - mark as keep playing
            if not prev_metadata['playing']:
                api.set_now_playing(prev_metadata, network)
                prev_metadata['playing'] = True

            # If it's a start of a listen - get time and mark as started playing
            if not started_playing:
                prev_metadata['timestamp'] = int(time.time())
                started_playing = True

            increase_playtime(prev_metadata, cur_metadata['playing'])

            handle_relistening(prev_metadata, network)

        # If song is the same but paused (increase will happen if last time checked song was playing)
        else:
            # Update UI if song was playing before
            if prev_metadata['playing']:
                update_queue(metadata_queue, False)

            prev_metadata['playing'] = False
            increase_playtime(prev_metadata, cur_metadata['playing'])
