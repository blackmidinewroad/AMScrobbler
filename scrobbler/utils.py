import sys

import numpy as np
import psutil
from PIL import Image, ImageDraw


def make_circle(img):
    """Return a circularly cropped version of the given image."""

    img = img.convert("RGB")
    np_image = np.array(img)
    w, h = img.size

    # Create alpha mask
    alpha = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(alpha)
    draw.pieslice([5, 5, w - 5, h - 5], 0, 360, fill=255)

    # Combine RGB image with alpha mask
    np_alpha = np.array(alpha)
    np_image = np.dstack((np_image, np_alpha))

    return Image.fromarray(np_image)


def is_gif(img) -> bool:
    """Check if image is a gif by checking if 'is_animated' in it's attributes."""

    return bool(getattr(img, "is_animated", False))


def get_process_id(process_name: str) -> int:
    """Get process ID (PID) of a process using it's name."""

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']

    return 0


def single_instance(process_name: str) -> None:
    """Make sure that only one instance of the app is running. If process is already running terminate program's execution."""

    n = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            n += 1
            if n == 2:
                sys.exit(1)


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to a maximum length, appending '...' if truncated."""

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3] + '...'
