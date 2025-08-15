import os
import sys
import time
import webbrowser
from pathlib import Path

import pylast
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from amscrobbler.filework import load_user_data, save_user_data
from amscrobbler.logic.lastfm.api import get_user_url

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')


# Send user to authentication web page, save session key, username and user's URL and return it with network
def auth_without_session_key():
    network = pylast.LastFMNetwork(API_KEY, API_SECRET)
    skg = pylast.SessionKeyGenerator(network)
    url = skg.get_web_auth_url()

    webbrowser.open(url)

    start = time.perf_counter()
    while True:
        try:
            # If user didn't log in 3 minutes
            if (time.perf_counter() - start) > 189:
                return ('Runtime Error', '')

            session_key, username = skg.get_web_auth_session_key_username(url)
            user_url = get_user_url(username, network)
            save_user_data(session_key, username, user_url)
            break
        except pylast.WSError:
            time.sleep(1)

    network.session_key = session_key

    return {'network': network, 'username': username, 'user_url': user_url}


# Authenticate user with session and return users data from json
def auth_with_session_key():
    network = pylast.LastFMNetwork(API_KEY, API_SECRET)
    user_data = load_user_data()
    network.session_key = user_data['session_key']
    user_data['network'] = network

    return user_data
