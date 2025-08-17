import atexit
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import logging

from scrobbler.filework import LOG_FILE
from scrobbler.gui.gui import App
from scrobbler.logic.main_logic import scrobble_at_exit
from scrobbler.utils import single_instance

logger = logging.getLogger(__name__)


def main():
    single_instance('AMScrobbler.exe')

    logging.basicConfig(level=logging.WARNING, filename=LOG_FILE, format='[%(asctime)s] %(levelname)s: %(message)s')

    app = App()
    atexit.register(scrobble_at_exit)
    app.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical('%s', e, exc_info=True)
        sys.exit(1)
