import sys
from datetime import timedelta
from pathlib import Path

from pywinauto import Application
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.utils import get_process_id


class AppScraper:
    def __init__(self):
        self.get_window()

    def get_window(self) -> None:
        """Get Apple Music window using process ID"""

        pid = get_process_id('AppleMusic.exe')
        if not pid:
            self.main_window = None
            return

        app = Application(backend='uia').connect(process=pid)
        self.main_window = app.window(title_re='.*Apple Music.*', visible_only=False)

    def convert_time_to_seconds(self, time_str: str) -> int:
        """Convert string time to seconds (e.g. '2:04' -> 124)"""

        window_time_list = time_str.split(':')
        minutes, seconds = int(window_time_list[-2]), int(window_time_list[-1])
        hours = 0 if len(window_time_list) == 2 else int(window_time_list[0])

        return timedelta(hours=hours, minutes=minutes, seconds=seconds).seconds

    def get_duration_from_window(self) -> int:
        """Get duration from progress bar of the song: get listening time and time left, then add them together"""

        try:
            cur_time = self.main_window.child_window(auto_id="CurrentTime", control_type="Text").window_text()
            time_left = self.main_window.child_window(auto_id="Duration", control_type="Text").window_text()[1:]
        except (ElementNotFoundError, ElementAmbiguousError, ValueError):
            return 0

        duration = self.convert_time_to_seconds(cur_time) + self.convert_time_to_seconds(time_left)

        return duration

    def get_data_from_AM_app(self, prev_id: str, is_app_duration: bool) -> dict:
        """Get data from Apple Music app using GUI"""

        if not self.main_window or not self.main_window.exists():
            self.get_window()

        if not self.main_window:
            return 'X'

        try:
            title = self.main_window.child_window(auto_id="myScrollViewer", control_type="Pane", found_index=0).window_text()
            artist, *album = (
                self.main_window.child_window(auto_id="myScrollViewer", control_type="Pane", found_index=1).window_text().split(' — ')
            )
            pause_play = self.main_window.child_window(auto_id="TransportControl_PlayPauseStop", control_type="Button").window_text()
        except (ElementNotFoundError, ElementAmbiguousError):
            return

        # Trying to get duration from progress bar if current duration is not from the app
        duration = 0 if is_app_duration else self.get_duration_from_window()

        song_id = f'{artist} - {title}'
        same_song = song_id == prev_id

        # If song is already playing - send only id, status and duration (to try to update it with app duration because it's the most accurate)
        song_metadata = {
            'id': song_id,
            'playing': True if pause_play in ('Pause', 'Приостановить') else False,
            'duration': duration,
            'is_app_duration': bool(duration),
            'same_song': same_song,
        }

        if not same_song:
            song_metadata.update(
                {
                    'title': title,
                    'artist': artist,
                    'album': album[0],
                    'playtime': 0,
                }
            )

        return song_metadata
