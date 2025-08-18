import sys
import threading
from pathlib import Path

import customtkinter as ctk

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from scrobbler import filework
from scrobbler.logic.lastfm.api import Lastfm


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

        self.label_font = ctk.CTkFont(family='SF Pro Display', size=30, weight='bold')
        self.label_retry_font = ctk.CTkFont(family='SF Pro Display', size=25)
        self.button_font = ctk.CTkFont(family='SF Pro Display', size=25)

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
            command=self.start_auth_thread,
            fg_color='#FF4E6B',
            hover_color="#E6455F",
            corner_radius=20,
            font=self.button_font,
            text_color_disabled=('#DCE4EE', '#DCE4EE'),
        )
        self.button.grid(row=2, column=0, pady=(0, 50))

    def start_auth_thread(self) -> None:
        self.button.configure(state='disabled', text='waiting...', fg_color='#E6455F')
        if self.login_retry_label:
            self.login_retry_label.destroy()

        self.auth_thread = threading.Thread(target=self.auth_process, daemon=True).start()

        self.poll_auth()

    def auth_process(self) -> None:
        if not filework.user_data_exists() or self.force_auth_without_sk:
            self.auth_complete = self.lastfm.auth_without_session_key()
            self.retry_msg = 'What took you so long?'
        else:
            self.auth_complete = self.lastfm.auth_with_session_key()
            if not self.auth_complete:
                self.force_auth_without_sk = True
                self.retry_msg = 'Something went wrong'

    def poll_auth(self) -> None:
        """Poll for auth to be completed. If auth unsuccessful let user try to log in again."""

        if self.auth_complete is not None:
            if self.auth_complete:
                self.button.configure(text='Logged in!', fg_color='#4CAF50')
                self.app.auth_complete()
            else:
                self.login_retry_label = ctk.CTkLabel(
                    self, width=200, height=100, text=f'{self.retry_msg}\nTry to log in again', font=self.label_retry_font
                )
                self.login_retry_label.grid(row=1, column=0, pady=(0, 20))
                self.button.configure(state='normal', text='Log in', fg_color='#FF4E6B')
                self.auth_complete = None
        else:
            self.after(500, self.poll_auth)
