import json
import os
import sys

from PIL import Image

from config import Config


def user_data_exists() -> bool:
    """Check if the user data JSON file exists.

    Returns:
        bool: True if exists, False otherwise.
    """

    return os.path.exists(Config.USER_DATA_FILE)


def load_user_data() -> dict | None:
    """Load user data from the JSON file.

    Returns:
        dict | None: User data if exists, None otherwise.
    """

    if user_data_exists():
        with open(Config.USER_DATA_FILE, encoding='utf-8') as file:
            return json.load(file)


def save_user_data(user_data: dict) -> None:
    """Save user data to the JSON file.

    Args:
        user_data (dict): The data to save.
    """

    with open(Config.USER_DATA_FILE, 'w', encoding='utf-8') as out_file:
        json.dump(user_data, out_file, indent=2)


def get_image_path(filename: str) -> str:
    """Get the absolute path to an image file, working both in normal Python and PyInstaller bundles.

    Args:
        filename (str): Name of the file with the image.

    Returns:
        str: Absolute path to the image.
    """

    if hasattr(sys, '_MEIPASS'):
        # Running in the PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath('.')

    return os.path.join(base_path, 'assets', filename)


def load_image(filename: str) -> Image.Image | None:
    """Load an image from file using PIL.

    Args:
        filename (str): Name of the file with the image.

    Returns:
        Image.Image | None: Loaded image, or None if file doesn't exist.
    """

    filepath = get_image_path(filename)

    if os.path.exists(filepath):
        with Image.open(filepath) as img:
            img.load()
            return img
