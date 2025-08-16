import atexit
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from scrobbler import filework
from scrobbler.gui.gui import App
from scrobbler.logic.main_logic import scrobble_at_exit
from scrobbler.utils import is_one_instance


def main():
    # Make sure that only one instance of the app is running
    if not is_one_instance('AMScrobbler.exe'):
        sys.exit(1)

    app = App()
    atexit.register(scrobble_at_exit)
    app.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        filework.log_error_to_file()
        sys.exit(1)
