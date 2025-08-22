import threading

import customtkinter as ctk

from scrobbler import filework
from scrobbler.logic.lastfm import Lastfm

from ..constants import Colors, Font


class LoginFrame(ctk.CTkFrame):
    """Login frame that initiates and manages user authentication with Last.fm.

    Provides a "Log in" button that triggers authentication in a background thread, updates UI feedback during the process,
    and notifies the main app when authentication completes.
    """

    def __init__(self, master, lastfm: Lastfm, force_auth_without_sk: bool = False):
        """Initialize the login frame.

        Creates `Log in` button fot user to log into Last.fm account.

        Args:
            master: Parent window (usually `App`).
            lastfm (Lastfm): Last.fm client used for authentication.
            force_auth_without_sk (bool, optional): If True, forces authentication without using a stored session key, even if one exists. 
                Defaults to False.
        """

        super().__init__(master)

        self.master = master
        self.lastfm = lastfm
        self.force_auth_without_sk = force_auth_without_sk

        self.auth_complete = None

        self.master.geometry('400x500')

        self.grid(row=0, column=0, padx=10, pady=(10, 10))
        self.configure(fg_color='transparent')

        self.label_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_LARGE, weight='bold')
        self.label_retry_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM)
        self.button_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM)

        self.login_label = ctk.CTkLabel(self, width=200, height=100, text='Apple Music\nlast.fm scrobbler', font=self.label_font)
        self.login_label.grid(row=0, column=0, pady=(0, 60))

        if self.force_auth_without_sk:
            self.login_retry_label = ctk.CTkLabel(
                self, width=200, height=100, text='Try to log in again', font=self.label_retry_font
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
        """Start authentication in a background thread and begin polling for completion."""

        self.button.configure(state='disabled', text='waiting...', fg_color=Colors.SECONDARY_PINK)
        if self.login_retry_label:
            self.login_retry_label.destroy()

        threading.Thread(target=self._auth_process, daemon=True).start()

        self._poll_auth()

    def _auth_process(self) -> None:
        """
        If there is no session key saved or `force_auth_without_sk` is True authenticate user through web,
        otherwise use saved session key.
        """

        if not filework.user_data_exists() or self.force_auth_without_sk:
            self.auth_complete = self.lastfm.auth_without_session_key()
        else:
            self.auth_complete = self.lastfm.auth_with_session_key()
            if not self.auth_complete:
                self.force_auth_without_sk = True

    def _poll_auth(self) -> None:
        """Check periodically whether authentication has completed.

        If successful:
            - Update button text to "Logged in!".
            - Notify main app via `auth_complete()` callback.
        If unsuccessful:
            - Show retry label and re-enable login button.
        If still pending:
            - Schedule another poll after 500 ms.
        """

        if self.auth_complete is not None:
            if self.auth_complete:
                self.button.configure(text='Logged in!', fg_color=Colors.GREEN)
                self.master.auth_complete()
            else:
                self.login_retry_label = ctk.CTkLabel(
                    self, width=200, height=100, text='Try to log in again', font=self.label_retry_font
                )
                self.login_retry_label.grid(row=1, column=0, pady=(0, 20))
                self.button.configure(state='normal', text='Log in', fg_color=Colors.MAIN_PINK)
                self.auth_complete = None
        else:
            self.after(500, self._poll_auth)
