from datetime import datetime
from warnings import filterwarnings
from os import getcwd
from os.path import join

from telegram import Update
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    Application,
    PicklePersistence,
    AIORateLimiter,
    Defaults,
)

from src.commands import get_all_handlers
from src.logger import setup_logger
from src.config import Config
from src.utils import startup, shutdown, error_handler
from src.utils.hooks import check_jobs


def main():
    logger = setup_logger()
    if logger:
        logger.info("Logger successfully initialized!")
    filterwarnings(
        action="ignore",
        message=r".*CallbackQueryHandler",
        category=PTBUserWarning,
    )
    defaults = Defaults(tzinfo=datetime.now().astimezone().tzinfo)

    application = (
        Application.builder()
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(20)
        .defaults(defaults)
        .token(Config.TOKEN.value)
        .rate_limiter(AIORateLimiter())
        .persistence(PicklePersistence(join(getcwd(), "context", "context")))
        .post_init(startup)
        .post_stop(shutdown)
        .build()
    )

    if not application:
        logger.fatal("Application not initialized!")
        exit(2)
    application.job_queue.run_repeating(check_jobs, interval=5)
    application.add_handlers(get_all_handlers())
    application.add_error_handler(error_handler)
    logger.info("Starting application!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
