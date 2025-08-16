import json
import os
import sys
from pathlib import Path

from PIL import Image

USER_HOME_DIR = os.path.expanduser('~')
AM_SCROBBLER_DATA_DIR = Path(os.path.join(USER_HOME_DIR, 'AMScrobbler'))
if not AM_SCROBBLER_DATA_DIR.exists():
    AM_SCROBBLER_DATA_DIR.mkdir(exist_ok=True)

USER_DATA_FILE = os.path.join(AM_SCROBBLER_DATA_DIR, 'lastfm_user_data.json')
LOG_FILE = os.path.join(AM_SCROBBLER_DATA_DIR, 'am_scrobbler.log')


# Load user's data from json
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, encoding='utf-8') as file:
            return json.load(file)


# Save user's data to json
def save_user_data(session_key, username, user_url):
    data = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, encoding='utf-8') as file:
            data = json.load(file)

    data['session_key'] = session_key
    data['username'] = username
    data['user_url'] = user_url

    with open(USER_DATA_FILE, 'w', encoding='utf-8') as out_file:
        json.dump(data, out_file, indent=2)


# Does file with user's data exists
def user_data_exists():
    return os.path.exists(USER_DATA_FILE)


# Get image file
def get_image_path(filename):
    if hasattr(sys, '_MEIPASS'):
        # Running in the PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath('.')

    return os.path.join(base_path, 'icons', filename)


# Load user's avatar
def load_image(filepath):
    if os.path.exists(filepath):
        with Image.open(filepath) as img:
            img.load()
            return img
