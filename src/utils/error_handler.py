from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes

logger = getLogger(__name__)


async def error_handler(_update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(
        "Exception caused while handling an update: ", exc_info=context.error
    )
