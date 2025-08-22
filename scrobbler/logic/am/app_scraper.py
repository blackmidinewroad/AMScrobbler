from pywinauto import Application
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

from scrobbler.utils import convert_time_to_seconds, get_process_id

from ..song import Song


class AppScraper:
    """Scraper for Apple Music Windows desktop app.

    Uses `pywinauto` to connect to the app window, extract metadata and update the `Song` object.
    """

    def __init__(self):
        self.main_window = None
        self._get_window()

    def _get_window(self) -> None:
        """Connect to the Apple Music window using process ID.

        Finds the process ID of `AppleMusic.exe` and attaches the `pywinauto` Application backend to it.
        Sets `self.main_window` to the matched window, or None if not found.
        """

        pid = get_process_id('AppleMusic.exe')
        if pid is None:
            self.main_window = None
            return

        app = Application(backend='uia').connect(process=pid)
        self.main_window = app.window(title_re='.*Apple Music.*', visible_only=False, found_index=0)

    def _get_duration_from_window(self) -> int:
        """Extract song duration from progress bar.

        Reads the current playtime (`CurrentTime`) and remaining time (`Duration`) UI elements from the Apple Music window,
        converts them to seconds, and sums them to estimate total track duration.

        Returns:
            int: Duration of the track in seconds, or 0 if extraction fails.
        """

        try:
            cur_time = self.main_window.child_window(auto_id='CurrentTime', control_type='Text').window_text()
            time_left = self.main_window.child_window(auto_id='Duration', control_type='Text').window_text().lstrip('-')
        except (ElementNotFoundError, ElementAmbiguousError, ValueError):
            return 0

        duration = convert_time_to_seconds(cur_time) + convert_time_to_seconds(time_left)

        return duration

    def update_metadata(self, song: Song) -> bool:
        """Update song metadata from the Apple Music app GUI.

        Extracts metadata directly from the app window and updates the given `Song`.

        Args:
            song (Song): Song object to update.

        Returns:
            bool: True if metadata was successfully updated, False otherwise.
        """

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

        id = f'{artist} - {title}'
        if song.is_same_song(id=id):
            # Trying to get duration from progress bar if current duration is not from the app
            duration = song.metadata['duration'] if song.metadata['is_app_duration'] else self._get_duration_from_window()
            song.metadata.update(
                {
                    'playing': True if pause_play in ('Pause', 'Приостановить') else False,
                    'duration': duration,
                    'is_app_duration': bool(duration),
                }
            )
        else:
            duration = self._get_duration_from_window()
            song.metadata.update(
                {
                    'title': title,
                    'artist': artist,
                    'id': id,
                    'album': album[0] if album else '',
                    'playing': True if pause_play in ('Pause', 'Приостановить') else False,
                    'duration': duration,
                    'is_app_duration': bool(duration),
                    'artwork': None,
                }
            )

        return True
