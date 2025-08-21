import atexit
import logging
import threading

import customtkinter as ctk

from config import Config
from scrobbler import filework
from scrobbler.logic import Song, run_background, scrobble_at_exit
from scrobbler.logic.lastfm import Lastfm

from .frames import LoginFrame, MainFrame, MinimalMainFrame
from .tray import Tray

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    """Main application window for AMScrobbler."""

    def __init__(self):
        """Initialize the application.

        - Configures main window (size, icon, theme, close behavior).
        - Initializes Last.fm API client and current `Song`.
        - Chooses login or main frame depending on whether user data exists.
        - Starts tray icon in a separate thread.
        - Registers a shutdown hook to scrobble at exit.
        """

        super().__init__()

        ctk.set_appearance_mode('dark')
        self.title('AMScrobbler')
        self.iconbitmap(filework.get_image_path('main_icon.ico'))
        self.geometry('400x500')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.withdraw)  # hides instead of closing
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lastfm = Lastfm()
        self.song = Song()

        if filework.user_data_exists():
            is_success = self.lastfm.auth_with_session_key()
            if is_success:
                self.show_main_frame()
            else:
                self.show_login_frame(force_auth_without_sk=True)
        else:
            self.show_login_frame()

        self.start_tray_icon_thread()

        atexit.register(scrobble_at_exit, self.song, self.lastfm)

    def show_login_frame(self, force_auth_without_sk: bool = False) -> None:
        """Display the login frame.

        Args:
            force_auth_without_sk (bool): If True, force re-authentication even if a stored session key exists.
        """

        self.login_frame = LoginFrame(self, self.lastfm, force_auth_without_sk=force_auth_without_sk)

    def show_main_frame(self) -> None:
        """Display the main frame.

        - If minimal GUI is enabled (`Config.MINIMAL_GUI`), show `MinimalMainFrame`.
        - Otherwise, set Last.fm avatar and show full `MainFrame`.
        - Starts background thread for scrobbling logic.
        """

        if Config.MINIMAL_GUI:
            self.main_frame = MinimalMainFrame(self, self.song, self.lastfm)
        else:
            self.lastfm.set_avatar()
            self.main_frame = MainFrame(self, self.song, self.lastfm)

        self.start_background_thread()

    def start_background_thread(self) -> None:
        threading.Thread(target=self._run_background_with_error_handling, daemon=True).start()

    def start_tray_icon_thread(self) -> None:
        self.tray = Tray(self)
        threading.Thread(target=self.tray.icon.run, daemon=True).start()

    def _run_background_with_error_handling(self) -> None:
        """Run scrobbling background logic handling errors.

        If error indicates an invalid session key, forces re-authentication without the session key.
        """

        try:
            run_background(self.song, self.lastfm)
        except Exception as e:
            logger.error('%s', e, exc_info=True)
            force_auth_without_sk = 'Invalid session key' in str(e)
            self.after(0, self._update_gui_on_error, force_auth_without_sk)

    def _update_gui_on_error(self, force_auth_without_sk: bool) -> None:
        """Destroy main frame and return to login frame after an error."""

        self.main_frame.destroy()
        self.show_login_frame(force_auth_without_sk=force_auth_without_sk)

    def auth_complete(self) -> None:
        """Callback executed after successful authentication. Destroys login frame and shows the main frame."""

        self.login_frame.destroy()
        self.show_main_frame()
