import sys
from pathlib import Path

import pylast

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from amscrobbler.utils import get_image_from_web, is_gif, make_circle


# Correct title and artist name if possible, get duration of a track
def get_more_metadata(metadata, network: pylast.LastFMNetwork):
    try:
        track = network.get_track(metadata['artist'], metadata['title'])
        artist = network.get_artist(metadata['artist'])

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


# Scrobble song
def scrobble_song(metadata, network: pylast.LastFMNetwork):
    for _ in range(5):
        try:
            network.scrobble(
                title=metadata['title'],
                artist=metadata['artist'],
                album=metadata['album'],
                timestamp=metadata['timestamp'],
            )
            break
        except pylast.NetworkError:
            continue


# Mark as now_playing on last.fm
def set_now_playing(metadata, network: pylast.LastFMNetwork):
    try:
        network.update_now_playing(
            title=metadata['title'],
            artist=metadata['artist'],
            album=metadata['album'],
            duration=metadata['duration'],
        )
    except pylast.NetworkError:
        pass


# Get user's avatar from last.fm
def get_avatar(username, network: pylast.LastFMNetwork):
    for _ in range(5):
        try:
            user = network.get_user(username)
            url = user.get_image()
            break
        except pylast.NetworkError:
            continue

    if not url:
        return

    img = get_image_from_web(url)
    if not img:
        return

    if not is_gif(img):
        img = make_circle(img)

    return img


# Get user's last.fm URL
def get_user_url(username, network: pylast.LastFMNetwork):
    user = network.get_user(username)
    return user.get_url()
