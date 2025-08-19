import pystray

from scrobbler import filework


class Tray(pystray.Icon):
    def __init__(self, app):
        super().__init__(app)

        self.app = app

        self.image = filework.load_image('combined_icon2.png')
        self.menu = pystray.Menu(
            pystray.MenuItem(text='Open', action=self.show_window, default=True), pystray.MenuItem('Exit', self.on_tray_quit)
        )
        self.icon = pystray.Icon('AMScrobbler', self.image, 'AMScrobbler', self.menu)

    def show_window(self):
        self.app.deiconify()

    def on_tray_quit(self, icon):
        icon.stop()
        self.app.quit()
