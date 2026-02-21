"""Allow running fluxion as `python -m fluxion`."""

from __future__ import annotations

import logging
import sys

from fluxion.cli.app import main

def setup_logging() -> None:
    """Setup root observability."""
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        logging.getLogger("fluxion.root").critical("Unhandled fatal error: %s", exc, exc_info=True)
        sys.exit(1)
