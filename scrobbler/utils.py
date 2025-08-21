import os
import sys
from datetime import timedelta

import numpy as np
import psutil
from PIL import Image, ImageDraw


def make_circle(img: Image.Image) -> Image.Image:
    """Return a circularly cropped version of the given image.

    Args:
        img (Image.Image): PIL image.

    Returns:
        Image.Image: circularly cropped image.
    """

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


def is_gif(img: Image.Image) -> bool:
    """Check if the given image is an animated GIF.

    Args:
        img (Image.Image): PIL image.

    Returns:
        bool: True if GIF, False otherwise.
    """

    return bool(getattr(img, "is_animated", False))


def get_process_id(process_name: str) -> int | None:
    """Get the process ID (PID) of a process by its name.

    Args:
        process_name (str): Name of the process.

    Returns:
        int | None: PID if found, otherwise None.
    """

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']


def get_executable_name() -> str | None:
    """Return the name of the current executable if running as a frozen .exe.

    Returns:
        str | None: Name of the executable or None if not running as a frozen .exe.
    """

    if getattr(sys, 'frozen', False):
        return os.path.basename(sys.executable)


def single_instance() -> None:
    """Ensure only one instance of the app is running.

    If more than one process with the name of the app is found, the program will terminate with exit code 1.
    """

    process_name = get_executable_name()
    if process_name is None:
        return

    n = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            n += 1

            # PyInstaller with `--onefile` runs two `.exe` with the same name, so if `n > 2` then not single instance
            if n > 2:
                sys.exit(1)


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to a maximum length, appending '...' if truncated.

    Args:
        text (str): Text to truncate.
        max_chars (int): Maximum allowed length of the resulting string.

    Returns:
        str: Truncated text with '...' appended if it exceeded max_chars.
    """

    return text if len(text) <= max_chars else text[: max_chars - 3] + '...'


def convert_time_to_seconds(time_str: str) -> int:
    """Convert a time string into seconds (e.g. '02:04' -> 124).

    Args:
        time_str (str): time in 'MM:SS' or 'HH:MM:SS' format.

    Returns:
        int: Total seconds.
    """

    window_time_list = time_str.split(':')
    minutes, seconds = int(window_time_list[-2]), int(window_time_list[-1])
    hours = 0 if len(window_time_list) == 2 else int(window_time_list[0])

    return timedelta(hours=hours, minutes=minutes, seconds=seconds).seconds
