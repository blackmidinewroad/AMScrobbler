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
    """Main app window."""

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode('dark')
        self.title('AMScrobbler')
        self.iconbitmap(filework.get_image_path('combined_icon2.ico'))
        self.geometry('400x500')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.withdraw)
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
        self.login_frame = LoginFrame(self, self.lastfm, force_auth_without_sk=force_auth_without_sk)

    def show_main_frame(self) -> None:
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
        try:
            run_background(self.song, self.lastfm)
        except Exception as e:
            logger.error('%s', e, exc_info=True)
            force_auth_without_sk = 'Invalid session key' in str(e)
            self.after(0, self._update_gui_on_error, force_auth_without_sk)

    def _update_gui_on_error(self, force_auth_without_sk: bool) -> None:
        self.main_frame.destroy()
        self.show_login_frame(force_auth_without_sk=force_auth_without_sk)

    def auth_complete(self) -> None:
        """Callback method used when auth in login frame is complete."""

        self.login_frame.destroy()
        self.show_main_frame()
