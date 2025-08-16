import logging
from io import BytesIO

import numpy as np
import psutil
import requests
from PIL import Image, ImageDraw
from requests.exceptions import HTTPError, RequestException, Timeout

logger = logging.getLogger(__name__)


# Crop a circle out of image
def make_circle(img):
    img = img.convert("RGB")
    np_image = np.array(img)
    h, w = img.size

    # Create same size alpha layer with circle
    alpha = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([5, 5, h - 5, w - 5], 0, 360, fill=255)

    np_alpha = np.array(alpha)
    np_image = np.dstack((np_image, np_alpha))

    return Image.fromarray(np_image)


# Check if image is a gif
def is_gif(img):
    try:
        return getattr(img, "is_animated", False)
    except:
        return


# Get process id of a process
def get_process_id(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']


# If more than one process runs return None, else return True
def is_one_instance(process_name):
    n = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            n += 1
            if n == 2:
                return
    return True


# Get image from web using URL
def get_image_from_web(url):
    try:
        response = requests.get(url, timeout=5, stream=True)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except (HTTPError, Timeout, RequestException):
        logger.warning("Couldn't fetch image, URL: %s", url, exc_info=True)
        return
