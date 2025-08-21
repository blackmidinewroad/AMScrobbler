import logging
import sys

from config import Config, ensure_directories
from scrobbler.gui import App
from scrobbler.utils import single_instance

logger = logging.getLogger(__name__)


def main():
    """Entry point of the application."""

    logging.basicConfig(level=logging.WARNING, filename=Config.LOG_FILE, format='[%(asctime)s] %(levelname)s: %(message)s', force=True)
    single_instance()
    ensure_directories()

    App().mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical('%s', e, exc_info=True)
        sys.exit(1)
