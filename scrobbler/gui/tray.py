import pystray

from scrobbler import filework


class Tray:
    """System tray icon with a context menu that allows the user to open the main window or quit the application."""

    def __init__(self, master):
        self.master = master

        image = filework.load_image('combined_icon2.png')
        menu = pystray.Menu(
            pystray.MenuItem(text='Open', action=self.show_window, default=True),
            pystray.MenuItem(text='Quit', action=self.on_tray_quit),
        )
        self.icon = pystray.Icon('AMScrobbler', image, 'AMScrobbler', menu)

    def show_window(self, icon=None, item=None) -> None:
        """Show (restore) the main application window from the tray."""

        self.master.deiconify()

    def on_tray_quit(self, icon, item=None) -> None:
        """Quit the application via tray menu. Stops the tray icon loop and terminates the main application."""

        icon.stop()
        self.master.quit()
