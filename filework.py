import json
import os
import sys
import traceback

from PIL import Image

USER_DATA_FILE = os.path.join(os.path.expanduser('~'), 'lastfm_user_data.json')


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
def is_user_data():
    return os.path.exists(USER_DATA_FILE)


# Get image file
def get_image_file(filename):
    if hasattr(sys, '_MEIPASS'):
        # Running in the PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath('.')

    return os.path.join(base_path, 'Icons', filename)


# Load user's avatar
def load_image(filepath):
    if os.path.exists(filepath):
        with Image.open(filepath) as img:
            img.load()
            return img


# Log all errors to file
def log_error_to_file(data=None):
    with open('error_log.txt', 'a', encoding='utf-8') as file:
        if not data:
            file.write(traceback.format_exc())
            file.write('\n')
        else:
            file.write(data)
            file.write('\n\n')
