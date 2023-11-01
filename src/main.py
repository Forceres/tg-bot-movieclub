from telegram import Update
from telegram.ext import Application
from telegraph.aio import Telegraph

from datetime import time

from src.commands import get_all_handlers
from src.logger.logger import setup_logger
from src.config import Config
from src.utils.date_helper import get_relative_date
from src.utils.hooks import startup, shutdown
from src.utils.error_handler import error_handler


def main():
    setup_logger()
    application = (
        Application.builder()
        .token(Config.TOKEN.value)
        .post_init(startup)
        .post_stop(shutdown)
        .build()
    )
    application.bot_data["telegraph"] = Telegraph()
    application.job_queue.run_daily(get_relative_date, time=time(hour=18))
    application.add_handlers(get_all_handlers())
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES, read_timeout=30)


if __name__ == "__main__":
    main()
