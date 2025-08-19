import webbrowser

import customtkinter as ctk
from PIL import Image

from scrobbler import filework
from scrobbler.logic import Song
from scrobbler.logic.lastfm import Lastfm
from scrobbler.utils import is_gif, truncate_text

from ..widgets import GIFLabel


class MainFrame(ctk.CTkFrame):
    def __init__(self, master, song: Song, lastfm: Lastfm):
        super().__init__(master)

        self.song = song

        self.playing_gif, self.title_label, self.artist_label = None, None, None
        self.master = master

        self.configure(fg_color='transparent')
        self.grid(row=0, column=0, padx=10, pady=(10, 10), sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # User header frame with user's name and avatar
        self.user_header_frame = ctk.CTkFrame(self)
        self.user_header_frame.configure(fg_color='#303030', corner_radius=20)
        self.user_header_frame.grid(row=0, column=0, pady=(0, 55), sticky='ne')
        self.user_header_frame.grid_columnconfigure(0, weight=1)

        img_w, img_h = 40, 40
        if not lastfm.avatar:
            img = Image.open(filework.get_image_path('placeholder_avatar.png'))
            avatar_image = ctk.CTkImage(img, size=(img_w, img_h))
            self.avatar_image_label = ctk.CTkLabel(self.user_header_frame, image=avatar_image, text='', cursor='hand2')
        elif is_gif(lastfm.avatar):
            self.avatar_image_label = GIFLabel(
                self.user_header_frame, lastfm.avatar, crop_circle=True, obj=True, width=img_w, height=img_h, cursor='hand2'
            )
        else:
            avatar_image = ctk.CTkImage(lastfm.avatar, size=(img_w, img_h))
            self.avatar_image_label = ctk.CTkLabel(self.user_header_frame, image=avatar_image, text='', cursor='hand2')

        self.avatar_image_label.grid(row=0, column=1, padx=(15, 10), pady=(5, 5), sticky='nsew')
        self.avatar_image_label.bind('<Button-1>', command=lambda x: webbrowser.open(lastfm.user_url))

        self.user_font = ctk.CTkFont(family='SF Pro Display', size=25)
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
        self.user_label.grid(row=0, column=0, padx=(10, 0), pady=(5, 5), sticky='nsew')

        # Frame where playing / paused gifs are displayed
        self.gif_frame = ctk.CTkFrame(self)
        self.gif_frame.configure(fg_color='transparent')
        self.gif_frame.grid(row=1, column=0, sticky='new')
        self.gif_frame.grid_columnconfigure(0, weight=1)
        self.gif_frame.grid_rowconfigure(0, weight=1)

        self.pause_gif_label = GIFLabel(self.gif_frame, filework.get_image_path('pause.gif'))
        self.pause_gif_label.grid(row=0, column=0)

        self.playing_gif = GIFLabel(self.gif_frame, filework.get_image_path('am_50.gif'), width=200, height=100)
        self.playing_gif.grid(row=0, column=0, pady=(30, 0))
        self.playing_gif.grid_remove()

        # Frame with artwork, song name and artist
        self.song_frame = ctk.CTkFrame(self)
        self.song_frame.configure(fg_color='transparent')
        self.song_frame.grid(row=2, column=0, sticky='new')
        self.song_frame.grid_columnconfigure(1, weight=1)

        self.artwork_image_label = ctk.CTkLabel(self.song_frame, text='')
        self.artwork_image_label.grid(row=0, column=0, rowspan=2, padx=(5, 5), pady=(5, 5), sticky='e')

        self.title_font = ctk.CTkFont(family='SF Pro Display', size=25, weight='bold')
        self.title_label = ctk.CTkLabel(self.song_frame, text='No music((', font=self.title_font)
        self.title_label.grid(row=0, column=1, padx=(0, 5), sticky='we')

        self.artist_font = ctk.CTkFont(family='SF Pro Display', size=20)
        self.artist_label = ctk.CTkLabel(self.song_frame, text='', font=self.artist_font, text_color='#A9A9A9')
        self.artist_label.grid(row=1, column=1, padx=(0, 5), sticky='we')

        self.update_now_playing(prev_id='', is_prev_playing=False, prev_artwork=None)

    # Set frame to now playing or no music
    def update_now_playing(self, prev_id, is_prev_playing, prev_artwork):
        if (
            self.song.metadata['id'] != prev_id
            or self.song.metadata['playing'] != is_prev_playing
            or self.song.metadata['artwork'] != prev_artwork
        ):
            if self.song.metadata['playing']:
                self.pause_gif_label.grid_remove()
                self.playing_gif.grid()

                self.song_frame.configure(fg_color='#303030')

                # Display song's artwork, if no artwork display placeholder image
                artwork = (
                    self.song.metadata['artwork'] if self.song.metadata['artwork'] is not None else filework.load_image('no_artwork.jpg')
                )
                artwork_image = ctk.CTkImage(artwork, size=(50, 50))

                self.title_font.configure(size=20)
                self.artwork_image_label.configure(image=artwork_image)
                self.artwork_image_label.grid()

                self.title_label.configure(text=truncate_text(self.song.metadata['title'], 30))
                self.title_label.grid()

                self.artist_label.configure(text=truncate_text(self.song.metadata['artist'], 33))
                self.artist_label.grid()
            else:
                if self.playing_gif.grid_info():
                    self.playing_gif.grid_remove()
                    self.pause_gif_label.grid()
                    self.song_frame.configure(fg_color='transparent')
                    self.title_font.configure(size=25)
                    self.title_label.configure(text='No music((')
                    self.artist_label.grid_remove()
                    self.artwork_image_label.grid_remove()

        self.after(1000, self.update_now_playing, self.song.metadata['id'], self.song.metadata['playing'], self.song.metadata['artwork'])
