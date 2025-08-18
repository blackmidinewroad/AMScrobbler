import sys
from pathlib import Path

import pystray

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from scrobbler import filework


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
