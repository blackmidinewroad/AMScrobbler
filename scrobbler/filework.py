import json
import os
import sys

from PIL import Image

from config import Config


def user_data_exists() -> bool:
    """Check if there is a file with user's data"""

    return os.path.exists(Config.USER_DATA_FILE)


def load_user_data():
    """Load user's data from json file"""

    if user_data_exists():
        with open(Config.USER_DATA_FILE, encoding='utf-8') as file:
            return json.load(file)


def save_user_data(user_data: dict) -> None:
    """Save user's data to json file"""

    with open(Config.USER_DATA_FILE, 'w', encoding='utf-8') as out_file:
        json.dump(user_data, out_file, indent=2)


def get_image_path(filename: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        # Running in the PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath('.')

    return os.path.join(base_path, 'icons', filename)


def load_image(filename: str):
    filepath = get_image_path(filename)

    if os.path.exists(filepath):
        with Image.open(filepath) as img:
            img.load()
            return img
