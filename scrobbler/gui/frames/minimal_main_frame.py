import webbrowser

import customtkinter as ctk
from PIL import Image

from scrobbler.filework import get_image_path
from scrobbler.logic import Song
from scrobbler.logic.lastfm import Lastfm
from scrobbler.utils import truncate_text

from ..constants import Colors, Font
from .login_frame import LoginFrame


class MinimalMainFrame(ctk.CTkFrame):
    """Minimal main frame displaying current user info and the currently playing song.

    A lightweight alternative to the full main frame:
    - Shows Last.fm username (clickable, links to profile).
    - Displays current track title and artist if playing.
    - Updates every second to reflect playback status.
    """

    def __init__(self, master, song: Song, lastfm: Lastfm):
        """Initialize the minimal main frame.

        Args:
            master: Parent window (usually `App`).
            song (Song): The Song object representing the current song.
            lastfm (Lastfm): Last.fm API client for user info.

        - Builds user header with username (clickable link).
        - Create relogin button.
        - Creates title/artist labels for now playing info.
        - Starts periodic updates.
        """

        super().__init__(master)

        self.song = song
        self.lastfm = lastfm

        master.geometry('400x150')

        self.configure(fg_color='transparent')
        self.grid(row=0, column=0, padx=10, pady=(10, 10), sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # User header frame with user's name
        self.user_header_frame = ctk.CTkFrame(self)
        self.user_header_frame.configure(fg_color=Colors.DARK_GRAY, corner_radius=20)
        self.user_header_frame.grid(row=0, column=0, pady=(0, 15), sticky='ne')
        self.user_header_frame.grid_columnconfigure(0, weight=1)

        self.user_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_SMALL)
        self.user_label = ctk.CTkLabel(
            self.user_header_frame,
            text=lastfm.username,
            font=self.user_font,
            text_color=Colors.MAIN_PINK,
            cursor='hand2',
        )
        self.user_label.bind('<Button-1>', lambda event: webbrowser.open(lastfm.user_url))
        self.user_label.bind("<Enter>", lambda event: self.user_label.configure(text_color=Colors.SECONDARY_PINK))
        self.user_label.bind("<Leave>", lambda event: self.user_label.configure(text_color=Colors.MAIN_PINK))
        self.user_label.grid(row=0, column=0, padx=(10, 10), pady=(5, 5), sticky='nsew')

        # Logut button
        self.logout_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.logout_frame.grid(row=0, column=0, pady=(0, 0), sticky='nw')
        self.logout_frame.grid_columnconfigure(0, weight=1)

        logout_img = ctk.CTkImage(Image.open(get_image_path('logout.png')), size=(30, 25))
        self.logout_image_label = ctk.CTkLabel(self.logout_frame, image=logout_img, text='', cursor='hand2')
        self.logout_image_label.grid(row=0, column=0, padx=(10, 10), pady=(5, 5), sticky='nsew')
        self.logout_image_label.bind('<Button-1>', self._relogin)

        # Frame with song's title and artist
        self.song_frame = ctk.CTkFrame(self)
        self.song_frame.configure(fg_color='transparent')
        self.song_frame.grid(row=1, column=0, sticky='new')
        self.song_frame.grid_columnconfigure(0, weight=1)

        self.pause_text = 'No music(('
        self.title_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM, weight='bold')
        self.title_label = ctk.CTkLabel(self.song_frame, text=self.pause_text, font=self.title_font)
        self.title_label.grid(row=0, column=0, padx=(0, 5), pady=(10, 0), sticky='we')

        self.artist_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_SMALL)
        self.artist_label = ctk.CTkLabel(self.song_frame, text='', font=self.artist_font, text_color=Colors.GRAY)
        self.artist_label.grid(row=1, column=0, padx=(0, 5), sticky='we')

        self._update_now_playing(prev_id='', is_prev_playing=False)

    def _update_now_playing(self, prev_id: str, is_prev_playing: bool) -> None:
        """Update displayed song info if app is visible and track or play status changed.

        Args:
            prev_id (str): ID of previously displayed song.
            is_prev_playing (bool): Whether the song was previously marked as playing.

        Behavior:
            - If a new song starts, update title and artist.
            - If playback stops, show pause message.
            - Reschedules itself every 1s with `after()`.
        """

        if self.winfo_ismapped() and (self.song.metadata['id'] != prev_id or self.song.metadata['playing'] != is_prev_playing):
            if self.song.metadata['playing']:
                self.title_font.configure(size=Font.SIZE_SMALL)
                self.title_label.configure(text=truncate_text(self.song.metadata['title'], 38))
                self.title_label.grid_configure(pady=(0, 0))

                self.artist_label.configure(text=truncate_text(self.song.metadata['artist'], 41))
                self.artist_label.grid()
            elif self.title_label.cget('text') != self.pause_text:
                self.title_font.configure(size=Font.SIZE_MEDIUM)
                self.title_label.configure(text=self.pause_text)
                self.title_label.grid_configure(pady=(10, 0))

                self.artist_label.grid_remove()

        if self.winfo_exists():
            if self.winfo_ismapped():
                self.after(1000, self._update_now_playing, self.song.metadata['id'], self.song.metadata['playing'])
            else:
                self.after(1000, self._update_now_playing, prev_id, is_prev_playing)

    def _relogin(self, event) -> None:
        """Destroy main frame and open login frame on `relogin` button click."""

        self.destroy()
        LoginFrame(self.master, self.lastfm, force_auth_without_sk=True)
