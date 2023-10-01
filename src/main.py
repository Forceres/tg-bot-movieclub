from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

from logger.logger import setup_logger
from config import Config
from utils.hooks import startup, shutdown


async def start(updater: Update, _context: ContextTypes.DEFAULT_TYPE):
    return await updater.message.reply_text("Hello, forceres!")


def main():
    setup_logger()
    application = (
        Application.builder()
        .token(Config.TOKEN.value)
        .post_init(startup)
        .post_stop(shutdown)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.run_polling()


if __name__ == "__main__":
    main()
