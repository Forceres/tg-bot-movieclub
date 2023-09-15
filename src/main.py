from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from os import getenv
from dotenv import load_dotenv
from logger.logger import setup_logger

load_dotenv()


async def start(updater: Update, context: ContextTypes.DEFAULT_TYPE):
    return await updater.message.reply_text("Hello, forceres!")


def main():
    setup_logger()
    application = Application.builder().token(getenv("TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()


if __name__ == "__main__":
    main()
