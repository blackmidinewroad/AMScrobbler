import threading

import customtkinter as ctk

from scrobbler import filework
from scrobbler.logic.lastfm import Lastfm

from ..constants import Colors, Font


class LoginFrame(ctk.CTkFrame):
    """Displays `log in` button that authenticates user."""

    def __init__(self, app, lastfm: Lastfm, force_auth_without_sk: bool = False):
        super().__init__(app)

        self.app = app
        self.lastfm = lastfm
        self.force_auth_without_sk = force_auth_without_sk

        self.auth_complete = None

        self.app.geometry('400x500')

        self.grid(row=0, column=0, padx=10, pady=(10, 10))
        self.configure(fg_color='transparent')

        self.label_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_LARGE, weight='bold')
        self.label_retry_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM)
        self.button_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM)

        self.login_label = ctk.CTkLabel(self, width=200, height=100, text='Apple Music\nlast.fm scrobbler', font=self.label_font)
        self.login_label.grid(row=0, column=0, pady=(0, 60))

        self.retry_msg = 'Something went wrong'

        if self.force_auth_without_sk:
            self.login_retry_label = ctk.CTkLabel(
                self, width=200, height=100, text=f'{self.retry_msg}\nTry to log in again', font=self.label_retry_font
            )
            self.login_retry_label.grid(row=1, column=0, pady=(0, 20))
        else:
            self.login_retry_label = None

        self.button = ctk.CTkButton(
            self,
            width=200,
            height=50,
            text='Log in',
            command=self._start_auth_thread,
            fg_color=Colors.MAIN_PINK,
            hover_color=Colors.SECONDARY_PINK,
            corner_radius=20,
            font=self.button_font,
            text_color_disabled=(Colors.WHITE, Colors.WHITE),
        )
        self.button.grid(row=2, column=0, pady=(0, 50))

    def _start_auth_thread(self) -> None:
        self.button.configure(state='disabled', text='waiting...', fg_color=Colors.SECONDARY_PINK)
        if self.login_retry_label:
            self.login_retry_label.destroy()

        self.auth_thread = threading.Thread(target=self._auth_process, daemon=True).start()

        self._poll_auth()

    def _auth_process(self) -> None:
        if not filework.user_data_exists() or self.force_auth_without_sk:
            self.auth_complete = self.lastfm.auth_without_session_key()
            self.retry_msg = 'What took you so long?'
        else:
            self.auth_complete = self.lastfm.auth_with_session_key()
            if not self.auth_complete:
                self.force_auth_without_sk = True
                self.retry_msg = 'Something went wrong'

    def _poll_auth(self) -> None:
        """Poll for auth to be completed. If auth unsuccessful let user try to log in again."""

        if self.auth_complete is not None:
            if self.auth_complete:
                self.button.configure(text='Logged in!', fg_color=Colors.GREEN)
                self.app.auth_complete()
            else:
                self.login_retry_label = ctk.CTkLabel(
                    self, width=200, height=100, text=f'{self.retry_msg}\nTry to log in again', font=self.label_retry_font
                )
                self.login_retry_label.grid(row=1, column=0, pady=(0, 20))
                self.button.configure(state='normal', text='Log in', fg_color=Colors.MAIN_PINK)
                self.auth_complete = None
        else:
            self.after(500, self._poll_auth)
