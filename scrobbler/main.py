import logging
import sys

from config import Config, ensure_directories

from .gui import App
from .utils import single_instance

logger = logging.getLogger(__name__)


def main():
    single_instance('AMScrobbler.exe')

    ensure_directories()

    logging.basicConfig(level=logging.WARNING, filename=Config.LOG_FILE, format='[%(asctime)s] %(levelname)s: %(message)s')

    app = App()
    app.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical('%s', e, exc_info=True)
        sys.exit(1)
