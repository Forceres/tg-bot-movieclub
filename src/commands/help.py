from telegram import Update
from telegram.ext import ContextTypes


async def get_help(updater: Update, _context: ContextTypes.DEFAULT_TYPE):
    return await updater.message.reply_text("Hello, forceres!")
