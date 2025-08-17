import atexit
import logging
import queue
import sys
import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk
import pystray
from PIL import Image
from pylast import WSError

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler import filework
from scrobbler.logic.lastfm.api import Lastfm
from scrobbler.logic.main_logic import run_background, scrobble_at_exit
from scrobbler.utils import is_gif, make_circle

logger = logging.getLogger(__name__)


# Login frame class. Has name of the app and button to log in
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, lastfm: Lastfm, retry=''):
        super().__init__(master)

        self.lastfm = lastfm
        self.is_success = None

        self.master = master
        self.master.geometry('400x500')

        self.retry = retry
        self.login_retry_label = None

        self.configure(fg_color='transparent')

        self.label_font = ctk.CTkFont(family='SF Pro Display', size=30, weight='bold')
        self.label_retry_font = ctk.CTkFont(family='SF Pro Display', size=25)
        self.button_font = ctk.CTkFont(family='SF Pro Display', size=25)

        self.login_label = ctk.CTkLabel(self, width=200, height=100, text='Apple Music\nlast.fm scrobbler', font=self.label_font)
        self.login_label.grid(row=0, column=0, pady=(0, 60))

        if self.retry:
            self.login_retry_label = ctk.CTkLabel(
                self, width=200, height=100, text='Something went wrong\nTry to log in again', font=self.label_retry_font
            )
            self.login_retry_label.grid(row=1, column=0, pady=(0, 20))

        self.button = ctk.CTkButton(
            self,
            width=200,
            height=50,
            text='Log in',
            command=self.start_auth_thread,
            fg_color='#FF4E6B',
            hover_color='#FF0436',
            corner_radius=20,
            font=self.button_font,
            text_color_disabled=('#DCE4EE', '#DCE4EE'),
        )
        self.button.grid(row=2, column=0, pady=(0, 50))

    def start_auth_thread(self):
        self.button.configure(state='disabled', text='waiting...', fg_color='#FF0436')
        if self.login_retry_label:
            self.login_retry_label.destroy()

        self.auth_thread = threading.Thread(target=self.auth_process, daemon=True).start()

        self.poll_user_data()

    def auth_process(self):
        if not filework.user_data_exists() or not self.retry or self.retry == 'force_auth_without_session_key':
            self.is_success = self.lastfm.auth_without_session_key()
            self.retry_msg = 'What took you so long?\n'
        else:
            self.is_success = self.lastfm.auth_with_session_key()
            if not self.is_success:
                self.retry = 'force_auth_without_session_key'
                self.retry_msg = ''

    # Checking if user logged in and we got user's data
    def poll_user_data(self):
        if self.is_success is not None:
            if self.is_success:
                self.button.configure(text='Logged in!', fg_color='#4CAF50')
                # Callback method to let app know that user logged in
                self.master.auth_complete()
            else:
                # Haven't received session key in 3 minutes, let user try to relogin
                self.login_retry_label = ctk.CTkLabel(
                    self, width=200, height=100, text=f'{self.retry_msg}Try to log in again', font=self.label_retry_font
                )
                self.login_retry_label.grid(row=1, column=0, pady=(0, 20))
                self.button.configure(state='normal', text='Log in', fg_color='#FF4E6B')
                self.is_success = None
        # Waiting for user to log in, check in again in 0.5 seconds
        else:
            self.after(500, self.poll_user_data)


# GIF label class to display gifs
class GIFLabel(ctk.CTkLabel):
    def __init__(self, master, img, crop_circle=False, obj=False, **kwargs):
        self._gif_image = img if obj else Image.open(img)

        kwargs.setdefault('width', self._gif_image.width)
        kwargs.setdefault('height', self._gif_image.height)
        kwargs.setdefault('text', '')
        self._duration = kwargs.pop("duration", None) or self._gif_image.info["duration"]
        self.crop_circle = crop_circle

        super().__init__(master, **kwargs)

        self._frames = []
        for i in range(self._gif_image.n_frames):
            self._gif_image.seek(i)
            if self.crop_circle:
                self._frames.append(ctk.CTkImage(make_circle(self._gif_image).copy(), size=(self['width'], self['height'])))
            else:
                self._frames.append(ctk.CTkImage(self._gif_image.copy(), size=(self['width'], self['height'])))

        self._animate()

        if not obj:
            self._gif_image.close()

    def _animate(self, idx=0):
        self.configure(image=self._frames[idx])
        self.after(self._duration, self._animate, (idx + 1) % len(self._frames))


def shorten_text(text, max_chars):
    return text if len(text) < max_chars else text[:max_chars] + '...'


# Main frame class
class MainFrame(ctk.CTkFrame):
    def __init__(self, master, lastfm: Lastfm):
        super().__init__(master)

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
        self.user_label.bind("<Enter>", command=lambda x: self.user_label.configure(text_color='#FF0436'))
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

    # Set frame to now playing or no music
    def update_now_playing(self, playing_now):
        if playing_now:
            self.pause_gif_label.grid_remove()
            self.playing_gif.grid()

            self.song_frame.configure(fg_color='#303030')

            # Display song's artwork, if no artwork display placeholder image
            artwork_image = ctk.CTkImage(playing_now.get('artwork', filework.load_image('no_artwork.jpg')), size=(50, 50))

            self.title_font.configure(size=20)
            self.artwork_image_label.configure(image=artwork_image)
            self.artwork_image_label.grid()

            self.title_label.configure(text=shorten_text(playing_now['title'], 26))
            self.title_label.grid()

            self.artist_label.configure(text=shorten_text(playing_now['artist'], 30))
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


# Minimalistic main frame class
class MinimalisticMainFrame(ctk.CTkFrame):
    def __init__(self, master, lastfm: Lastfm):
        super().__init__(master)

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
        self.user_label.bind("<Enter>", command=lambda x: self.user_label.configure(text_color='#FF0436'))
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

    # Set frame to now playing or no music
    def update_now_playing(self, playing_now):
        if playing_now:
            self.title_font.configure(size=20)

            self.title_label.configure(text=shorten_text(playing_now['title'], 35))
            self.title_label.grid_configure(pady=(0, 0))
            self.title_label.grid()

            self.artist_label.configure(text=shorten_text(playing_now['artist'], 38))
            self.artist_label.grid()
        else:
            if not self.title_label.cget('text') == self.pause_text:
                self.title_font.configure(size=25)
                self.title_label.configure(text=self.pause_text)
                self.title_label.grid_configure(pady=(10, 0))
                self.artist_label.grid_remove()


# Tray class
class Tray(pystray.Icon):
    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.image = filework.load_image('combined_icon2.png')
        self.menu = pystray.Menu(
            pystray.MenuItem(text='Open', action=self.show_window, default=True), pystray.MenuItem('Exit', self.on_tray_quit)
        )
        self.icon = pystray.Icon('AMScrobbler', self.image, 'AMScrobbler', self.menu)

    def show_window(self):
        self.master.deiconify()

    def on_tray_quit(self, icon):
        icon.stop()
        self.master.quit()


# Main app class
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

        self.error_queue, self.song_queue = queue.Queue(), queue.Queue()

        self.lastfm = Lastfm()

        if filework.user_data_exists():
            is_success = self.lastfm.auth_with_session_key()
            if is_success:
                self.show_main_frame()
            else:
                self.show_login_frame(retry='force_auth_without_session_key')
        else:
            self.show_login_frame()

        self.start_tray_icon_thread()

        self.poll_song()
        self.check_for_errors()

        atexit.register(scrobble_at_exit, self.lastfm)

    def show_login_frame(self, retry=False):
        self.login_frame = LoginFrame(self, self.lastfm, retry)
        self.login_frame.grid(row=0, column=0, padx=10, pady=(10, 10))

    def show_main_frame(self):
        # # Add user's avatar to data (not minimalistic)
        # self.lastfm.set_avatar()

        # self.main_frame = MainFrame(self, self.lastfm)

        self.main_frame = MinimalisticMainFrame(self, self.lastfm)

        self.minimalistic = True

        self.background_thread = self.start_background_thread()

    def auth_complete(self):
        self.login_frame.destroy()
        self.show_main_frame()

    def start_background_thread(self):
        threading.Thread(target=self.run_background_with_error_handling, args=[self.song_queue], daemon=True).start()

    def start_tray_icon_thread(self):
        self.tray_icon = Tray(self).icon
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()

    def run_background_with_error_handling(self, song_queue):
        try:
            run_background(song_queue, self.minimalistic, self.lastfm)
        except Exception as e:
            logger.error('%s', e, exc_info=True)
            self.error_queue.put(e)

    # Check if there are any errors in the background. Try to relogin if error
    def check_for_errors(self):
        try:
            error = self.error_queue.get_nowait()
            self.main_frame.destroy()
            if 'Invalid session key' in str(error):
                retry_message = 'force_auth_without_session_key'
            else:
                retry_message = 'Unknown'
            self.show_login_frame(retry=retry_message)
        except queue.Empty:
            pass

        self.after(5000, self.check_for_errors)

    # Get current playing song
    def poll_song(self):
        try:
            playing_now = self.song_queue.get_nowait()
            self.main_frame.update_now_playing(playing_now)
        except queue.Empty:
            pass

        # Continue polling
        self.after(500, self.poll_song)
