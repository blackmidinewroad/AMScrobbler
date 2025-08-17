import sys
import time
import webbrowser
from pathlib import Path

import pylast

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from scrobbler.filework import load_user_data, save_user_data
from scrobbler.logic.lastfm.api import get_user_url


# Send user to authentication web page, save session key, username and user's URL and return it with network
def auth_without_session_key():
    network = pylast.LastFMNetwork(Config.API_KEY, Config.API_SECRET)
    skg = pylast.SessionKeyGenerator(network)
    url = skg.get_web_auth_url()

    webbrowser.open(url)

    start = time.perf_counter()
    while True:
        try:
            # If user didn't log in 3 minutes
            if (time.perf_counter() - start) >= 180:
                return {'expired': True}

            session_key, username = skg.get_web_auth_session_key_username(url)
            user_url = get_user_url(username, network)

            user_data = {
                'session_key': session_key,
                'username': username,
                'user_url': user_url,
            }
            save_user_data(user_data)

            break
        except pylast.WSError:
            time.sleep(1)

    network.session_key = session_key

    return {'network': network, 'username': username, 'user_url': user_url}


# Authenticate user with session and return users data from json
def auth_with_session_key():
    network = pylast.LastFMNetwork(Config.API_KEY, Config.API_SECRET)
    user_data = load_user_data()
    network.session_key = user_data['session_key']
    user_data['network'] = network

    return user_data
