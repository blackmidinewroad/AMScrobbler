import webbrowser

import customtkinter as ctk

from scrobbler.logic import Song
from scrobbler.logic.lastfm import Lastfm
from scrobbler.utils import truncate_text

from ..constants import Colors, Font


class MinimalMainFrame(ctk.CTkFrame):
    def __init__(self, master, song: Song, lastfm: Lastfm):
        super().__init__(master)

        self.song = song

        self.title_label, self.artist_label = None, None
        self.master = master

        self.master.geometry('400x150')

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
        self.user_label.bind('<Button-1>', command=lambda x: webbrowser.open(lastfm.user_url))
        self.user_label.bind("<Enter>", command=lambda x: self.user_label.configure(text_color=Colors.SECONDARY_PINK))
        self.user_label.bind("<Leave>", command=lambda x: self.user_label.configure(text_color=Colors.MAIN_PINK))
        self.user_label.grid(row=0, column=0, padx=(10, 10), pady=(5, 5), sticky='nsew')

        # Frame with song name and artist
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

    # Set frame to now playing or no music
    def _update_now_playing(self, prev_id, is_prev_playing):
        if self.song.metadata['id'] != prev_id or self.song.metadata['playing'] != is_prev_playing:
            if self.song.metadata['playing']:
                self.title_font.configure(size=Font.SIZE_SMALL)

                self.title_label.configure(text=truncate_text(self.song.metadata['title'], 38))
                self.title_label.grid_configure(pady=(0, 0))
                self.title_label.grid()

                self.artist_label.configure(text=truncate_text(self.song.metadata['artist'], 41))
                self.artist_label.grid()
            else:
                if not self.title_label.cget('text') == self.pause_text:
                    self.title_font.configure(size=Font.SIZE_MEDIUM)
                    self.title_label.configure(text=self.pause_text)
                    self.title_label.grid_configure(pady=(10, 0))
                    self.artist_label.grid_remove()

        self.after(1000, self._update_now_playing, self.song.metadata['id'], self.song.metadata['playing'])
