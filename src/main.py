from warnings import filterwarnings

from telegram import Update
from telegram.warnings import PTBUserWarning
from telegram.ext import Application
from telegraph.aio import Telegraph

from src.commands import get_all_handlers
from src.logger.logger import setup_logger
from src.config import Config
from src.utils.hooks import startup, shutdown
from src.utils.error_handler import error_handler


def main():
    setup_logger()
    filterwarnings(
        action="ignore",
        message=r".*CallbackQueryHandler",
        category=PTBUserWarning,
    )
    application = (
        Application.builder()
        .get_updates_read_timeout(30)
        .token(Config.TOKEN.value)
        .post_init(startup)
        .post_stop(shutdown)
        .build()
    )
    application.bot_data["telegraph"] = Telegraph()
    application.add_handlers(get_all_handlers())
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
