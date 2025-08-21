import webbrowser

import customtkinter as ctk
from PIL import Image

from scrobbler import filework
from scrobbler.logic import Song
from scrobbler.logic.lastfm import Lastfm
from scrobbler.utils import is_gif, truncate_text

from ..constants import Colors, Font
from ..widgets import GIFLabel
from .login_frame import LoginFrame


class MainFrame(ctk.CTkFrame):
    """Main frame displaying user info and the currently playing song.

    Includes:
        - User avatar and username (clickable, opens profile in browser).
        - Relogin button.
        - Animated GIFs indicating play/pause state.
        - Song metadata (artwork, title, and artist).

    Dynamically updates to reflect changes in song metadata.
    """

    def __init__(self, master, song: Song, lastfm: Lastfm):
        """Initialize the main frame.

        Args:
            master: Parent window (usually `App`).
            song (Song): The Song object representing the current song.
            lastfm (Lastfm): Last.fm API client for user info.

        - Builds user header with username and avatar (clickable link).
        - Create relogin button.
        - Creates play/pause labels with animated GIFs to indicate play/pause state.
        - Creates title/artist labels for now playing info.
        - Starts periodic updates.
        """

        super().__init__(master)

        self.song = song
        self.lastfm = lastfm

        self.configure(fg_color='transparent')
        self.grid(row=0, column=0, padx=10, pady=(10, 10), sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # User header frame with user's name and avatar
        self.user_header_frame = ctk.CTkFrame(self, fg_color=Colors.DARK_GRAY, corner_radius=20)
        self.user_header_frame.grid(row=0, column=0, pady=(0, 55), sticky='ne')
        self.user_header_frame.grid_columnconfigure(0, weight=1)

        img_w, img_h = 40, 40
        if not lastfm.avatar:
            img = Image.open(filework.get_image_path('placeholder_avatar.png'))
            avatar_image = ctk.CTkImage(img, size=(img_w, img_h))
            self.avatar_image_label = ctk.CTkLabel(self.user_header_frame, image=avatar_image, text='', cursor='hand2')
        elif is_gif(lastfm.avatar):
            self.avatar_image_label = GIFLabel(
                self.user_header_frame, lastfm.avatar, crop_circle=True, width=img_w - 7, height=img_h - 7, text='', cursor='hand2'
            )
        else:
            avatar_image = ctk.CTkImage(lastfm.avatar, size=(img_w, img_h))
            self.avatar_image_label = ctk.CTkLabel(self.user_header_frame, image=avatar_image, text='', cursor='hand2')

        self.avatar_image_label.grid(row=0, column=1, padx=(15, 10), pady=(5, 5), sticky='nsew')
        self.avatar_image_label.bind('<Button-1>', lambda event: webbrowser.open(lastfm.user_url))

        if is_gif(lastfm.avatar):
            self.avatar_image_label.animate()

        self.user_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM)
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
        self.user_label.grid(row=0, column=0, padx=(10, 0), pady=(5, 5), sticky='nsew')

        # Logut button
        self.logout_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.logout_frame.grid(row=0, column=0, pady=(7, 55), sticky='nw')
        self.logout_frame.grid_columnconfigure(0, weight=1)

        logout_img = ctk.CTkImage(Image.open(filework.get_image_path('logout.png')), size=(30, 25))
        self.logout_image_label = ctk.CTkLabel(self.logout_frame, image=logout_img, text='', cursor='hand2')
        self.logout_image_label.grid(row=0, column=0, padx=(10, 10), pady=(5, 5), sticky='nsew')
        self.logout_image_label.bind('<Button-1>', self._relogin)

        # Frame with playing/paused gifs
        self.gif_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.gif_frame.grid(row=1, column=0, sticky='new')
        self.gif_frame.grid_columnconfigure(0, weight=1)
        self.gif_frame.grid_rowconfigure(0, weight=1)

        with Image.open(filework.get_image_path('pause.gif')) as pause_gif:
            self.pause_gif = GIFLabel(self.gif_frame, pause_gif)
        self.pause_gif.grid(row=0, column=0)
        self.pause_gif.grid_remove()

        with Image.open(filework.get_image_path('play.gif')) as play_gif:
            self.play_gif = GIFLabel(self.gif_frame, play_gif, width=200, height=100)
        self.play_gif.grid(row=0, column=0, pady=(30, 0))
        self.play_gif.grid_remove()

        self._show_pause_gif()

        # Frame with song's artwork, title and artist
        self.song_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.song_frame.grid(row=2, column=0, sticky='new')
        self.song_frame.grid_columnconfigure(1, weight=1)

        self.artwork_image_label = ctk.CTkLabel(self.song_frame, text='')
        self.artwork_image_label.grid(row=0, column=0, rowspan=2, padx=(5, 5), pady=(5, 5), sticky='e')
        self.placeholder_artwork = filework.load_image('placeholder_artwork.jpg')

        self.title_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_MEDIUM, weight='bold')
        self.title_label = ctk.CTkLabel(self.song_frame, text='No music((', font=self.title_font)
        self.title_label.grid(row=0, column=1, padx=(0, 5), sticky='we')

        self.artist_font = ctk.CTkFont(family=Font.FAMILY, size=Font.SIZE_SMALL)
        self.artist_label = ctk.CTkLabel(self.song_frame, text='', font=self.artist_font, text_color=Colors.GRAY)
        self.artist_label.grid(row=1, column=1, padx=(0, 5), sticky='we')

        self._update_now_playing(prev_id='', is_prev_playing=False, prev_artwork=None)

    def _update_now_playing(self, prev_id: str, is_prev_playing: bool, prev_artwork) -> None:
        """Update displayed song info if metadata changed.

        Triggers re-render when:
            - Song ID changes (new track).
            - Play/pause state changes.
            - Artwork changes (artwork can arrive later than title/artist).

        Args:
            prev_id (str): Previously displayed song ID.
            is_prev_playing (bool): Previous play state.
            prev_artwork: Previously displayed artwork image.
        """

        if (
            self.song.metadata['id'] != prev_id
            or self.song.metadata['playing'] != is_prev_playing
            or self.song.metadata['artwork'] != prev_artwork
        ):
            if self.song.metadata['playing']:
                self._show_play_gif()

                self.song_frame.configure(fg_color=Colors.DARK_GRAY)

                artwork = self.song.metadata['artwork'] if self.song.metadata['artwork'] is not None else self.placeholder_artwork
                artwork_image = ctk.CTkImage(artwork, size=(50, 50))
                self.artwork_image_label.configure(image=artwork_image)
                self.artwork_image_label.grid()

                self.title_font.configure(size=Font.SIZE_SMALL)
                self.title_label.configure(text=truncate_text(self.song.metadata['title'], 30))

                self.artist_label.configure(text=truncate_text(self.song.metadata['artist'], 33))
                self.artist_label.grid()
            elif self.play_gif.winfo_manager():
                self._show_pause_gif()

                self.song_frame.configure(fg_color='transparent')
                self.title_font.configure(size=Font.SIZE_MEDIUM)
                self.title_label.configure(text='No music((')

                self.artist_label.grid_remove()
                self.artwork_image_label.grid_remove()

        if self.winfo_exists():
            self.after(
                1000, self._update_now_playing, self.song.metadata['id'], self.song.metadata['playing'], self.song.metadata['artwork']
            )

    def _show_pause_gif(self) -> None:
        """Display and animate the pause GIF if not already displayed and hide the play GIF."""

        if not self.pause_gif.winfo_manager():
            self.play_gif.grid_remove()
            self.pause_gif.grid()
            self.pause_gif.animate()

    def _show_play_gif(self) -> None:
        """Display and animate the play GIF if not already displayed and hide the pause GIF."""

        if not self.play_gif.winfo_manager():
            self.pause_gif.grid_remove()
            self.play_gif.grid()
            self.play_gif.animate()

    def _relogin(self, event) -> None:
        """Destroy main frame and open login frame on `relogin` button click."""

        self.destroy()
        LoginFrame(self.master, self.lastfm, force_auth_without_sk=True)
