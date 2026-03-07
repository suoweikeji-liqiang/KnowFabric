"""Worker service entry point."""
import logging
from packages.core.config import settings
from packages.core.logging import setup_logging

# Setup logging
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    """Worker main entry point."""
    logger.info("Worker service starting", extra={"service": "worker"})

    # Worker will be implemented in subsequent issues
    # For now, just a placeholder that can start

    logger.info("Worker service ready", extra={"service": "worker"})


if __name__ == "__main__":
    main()
