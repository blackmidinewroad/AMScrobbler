import atexit
import logging
import sys
import threading
from pathlib import Path

import customtkinter as ctk

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler import filework
from scrobbler.gui.frames import login_frame, main_frame, minimal_main_frame
from scrobbler.gui.tray import Tray
from scrobbler.logic.lastfm.api import Lastfm
from scrobbler.logic.main_logic import run_background, scrobble_at_exit
from scrobbler.logic.song import Song

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode('dark')
        self.title('AMScrobbler')
        self.iconbitmap(filework.get_image_path('combined_icon2.ico'))
        self.geometry('400x500')
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.hide_window)
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

    def show_login_frame(self, force_auth_without_sk=False):
        self.login_frame = login_frame.LoginFrame(self, self.lastfm, force_auth_without_sk=force_auth_without_sk)

    def show_main_frame(self):
        # self.lastfm.set_avatar()
        # self.main_frame = main_frame.MainFrame(self, self.song, self.lastfm)
        # self.minimalistic = False

        self.main_frame = minimal_main_frame.MinimalisticMainFrame(self, self.song, self.lastfm)
        self.minimalistic = True

        self.start_background_thread()

    def auth_complete(self):
        self.login_frame.destroy()
        self.show_main_frame()

    def start_background_thread(self):
        threading.Thread(target=self.run_background_with_error_handling, daemon=True).start()

    def start_tray_icon_thread(self):
        self.tray_icon = Tray(self).icon
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()

    def run_background_with_error_handling(self):
        try:
            run_background(self.minimalistic, self.song, self.lastfm)
        except Exception as e:
            logger.error('%s', e, exc_info=True)
            force_auth_without_sk = 'Invalid session key' in str(e)

            self.after(0, self._update_gui_on_error, force_auth_without_sk)

    def _update_gui_on_error(self, force_auth_without_sk):
        self.main_frame.destroy()
        self.show_login_frame(force_auth_without_sk=force_auth_without_sk)
