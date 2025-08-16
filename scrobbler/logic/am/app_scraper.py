import sys
from datetime import timedelta
from pathlib import Path

from pywinauto import Application
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.utils import get_process_id


# Get Apple Music window with process ID
def get_window():
    pid = get_process_id('AppleMusic.exe')
    if not pid:
        return
    app = Application(backend='uia').connect(process=pid)
    return app.window(title_re='.*Apple Music.*', visible_only=False)


# Convert string time from window to timedelta
def get_time_from_window(window_time):
    window_time_list = window_time.split(':')
    minutes, seconds = int(window_time_list[-2]), int(window_time_list[-1])
    hours = 0 if len(window_time_list) == 2 else int(window_time_list[0])
    return timedelta(hours=hours, minutes=minutes, seconds=seconds).seconds


# Fetch data from Apple Music app
def get_data_from_AM_app(prev_id, is_app_duration):
    main_window = get_window()
    if not main_window:
        return 'X'

    try:
        title = main_window.child_window(auto_id="myScrollViewer", control_type="Pane", found_index=0).window_text()
        artist, *album = main_window.child_window(auto_id="myScrollViewer", control_type="Pane", found_index=1).window_text().split(' — ')
        pause_play = main_window.child_window(auto_id="TransportControl_PlayPauseStop", control_type="Button").window_text()
    except (ElementNotFoundError, ElementAmbiguousError):
        return

    # Trying to get duration from progress bar only when the song first time played
    duration = 0
    if not is_app_duration:
        try:
            cur_time = get_time_from_window(main_window.child_window(auto_id="CurrentTime", control_type="Text").window_text())
            time_left = get_time_from_window(main_window.child_window(auto_id="Duration", control_type="Text").window_text()[1:])
            duration = cur_time + time_left
        except (ElementNotFoundError, ElementAmbiguousError, ValueError):
            pass

    # If song is already playing send only id and status
    song_id = f'{artist} - {title}'
    same_song = song_id == prev_id
    if same_song:
        song_metadata = {
            'id': song_id,
            'playing': True if pause_play in ('Pause', 'Приостановить') else False,
            'duration': duration,
            'is_app_duration': bool(duration),
            'same_song': same_song,
        }
    else:
        song_metadata = {
            'id': song_id,
            'title': title,
            'artist': artist,
            'album': album[0],
            'playing': True if pause_play in ('Pause', 'Приостановить') else False,
            'duration': duration,
            'is_app_duration': bool(duration),
            'playtime': 0,
            'same_song': same_song,
        }

    return song_metadata
