import sys
import webbrowser
from pathlib import Path

import customtkinter as ctk

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler.logic.lastfm.api import Lastfm
from scrobbler.logic.song import Song
from scrobbler.utils import truncate_text


class MinimalisticMainFrame(ctk.CTkFrame):
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
        self.user_header_frame.configure(fg_color='#303030', corner_radius=20)
        self.user_header_frame.grid(row=0, column=0, pady=(0, 15), sticky='ne')
        self.user_header_frame.grid_columnconfigure(0, weight=1)

        self.user_font = ctk.CTkFont(family='SF Pro Display', size=20)
        self.user_label = ctk.CTkLabel(
            self.user_header_frame,
            text=lastfm.username,
            font=self.user_font,
            text_color='#FF4E6B',
            cursor='hand2',
        )
        self.user_label.bind('<Button-1>', command=lambda x: webbrowser.open(lastfm.user_url))
        self.user_label.bind("<Enter>", command=lambda x: self.user_label.configure(text_color='#E6455F'))
        self.user_label.bind("<Leave>", command=lambda x: self.user_label.configure(text_color='#FF4E6B'))
        self.user_label.grid(row=0, column=0, padx=(10, 10), pady=(5, 5), sticky='nsew')

        # Frame with song name and artist
        self.song_frame = ctk.CTkFrame(self)
        self.song_frame.configure(fg_color='transparent')
        self.song_frame.grid(row=1, column=0, sticky='new')
        self.song_frame.grid_columnconfigure(0, weight=1)

        self.pause_text = 'No music(('
        self.title_font = ctk.CTkFont(family='SF Pro Display', size=25, weight='bold')
        self.title_label = ctk.CTkLabel(self.song_frame, text=self.pause_text, font=self.title_font)
        self.title_label.grid(row=0, column=0, padx=(0, 5), pady=(10, 0), sticky='we')

        self.artist_font = ctk.CTkFont(family='SF Pro Display', size=20)
        self.artist_label = ctk.CTkLabel(self.song_frame, text='', font=self.artist_font, text_color='#A9A9A9')
        self.artist_label.grid(row=1, column=0, padx=(0, 5), sticky='we')

        self.update_now_playing(prev_id='', is_prev_playing=False)

    # Set frame to now playing or no music
    def update_now_playing(self, prev_id, is_prev_playing):
        if self.song.metadata['id'] != prev_id or self.song.metadata['playing'] != is_prev_playing:
            if self.song.metadata['playing']:
                self.title_font.configure(size=20)

                self.title_label.configure(text=truncate_text(self.song.metadata['title'], 35))
                self.title_label.grid_configure(pady=(0, 0))
                self.title_label.grid()

                self.artist_label.configure(text=truncate_text(self.song.metadata['artist'], 38))
                self.artist_label.grid()
            else:
                if not self.title_label.cget('text') == self.pause_text:
                    self.title_font.configure(size=25)
                    self.title_label.configure(text=self.pause_text)
                    self.title_label.grid_configure(pady=(10, 0))
                    self.artist_label.grid_remove()

        self.after(1000, self.update_now_playing, self.song.metadata['id'], self.song.metadata['playing'])
