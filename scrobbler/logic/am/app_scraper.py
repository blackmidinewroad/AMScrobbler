from pywinauto import Application
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

from scrobbler.utils import convert_time_to_seconds, get_process_id

from ..song import Song


class AppScraper:
    def __init__(self):
        self.main_window = None
        self._get_window()

    def _get_window(self) -> None:
        """Get Apple Music window using process ID."""

        pid = get_process_id('AppleMusic.exe')
        if not pid:
            self.main_window = None
            return

        app = Application(backend='uia').connect(process=pid)
        self.main_window = app.window(title_re='.*Apple Music.*', visible_only=False)

    def _get_duration_from_window(self) -> int:
        """Get duration from progress bar of a song: get listening time and time left, then add them together."""

        try:
            cur_time = self.main_window.child_window(auto_id='CurrentTime', control_type='Text').window_text()
            time_left = self.main_window.child_window(auto_id='Duration', control_type='Text').window_text()[1:]
        except (ElementNotFoundError, ElementAmbiguousError, ValueError):
            return 0

        duration = convert_time_to_seconds(cur_time) + convert_time_to_seconds(time_left)

        return duration

    def update_metadata(self, song: Song) -> bool:
        """Update song metadata from Apple Music app using GUI."""

        if not self.main_window or not self.main_window.exists():
            self._get_window()

        if not self.main_window:
            return False

        try:
            title = self.main_window.child_window(auto_id='myScrollViewer', control_type='Pane', found_index=0).window_text()
            artist, *album = (
                self.main_window.child_window(auto_id='myScrollViewer', control_type='Pane', found_index=1).window_text().split(' — ')
            )
            pause_play = self.main_window.child_window(auto_id='TransportControl_PlayPauseStop', control_type='Button').window_text()
        except (ElementNotFoundError, ElementAmbiguousError):
            return False

        # Trying to get duration from progress bar if current duration is not from the app
        duration = song.metadata['duration'] if song.metadata['is_app_duration'] else self._get_duration_from_window()

        song.metadata.update(
            {
                'title': title,
                'artist': artist,
                'id': f'{artist} - {title}',
                'album': album[0],
                'duration': duration,
                'is_app_duration': bool(duration),
                'playing': True if pause_play in ('Pause', 'Приостановить') else False,
            }
        )

        return True
