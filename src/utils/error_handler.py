import asyncio
from logging import getLogger

from telegram import Update
from telegram.error import BadRequest, RetryAfter, TelegramError
from telegram.ext import CallbackContext


logger = getLogger(__name__)


async def error_handler(_update: Update, context: CallbackContext):
    if isinstance(context.error, RetryAfter):
        logger.error(
            "RetryAfter Exception", exc_info=(RetryAfter, context.error, None)
        )
        await asyncio.sleep(context.error.retry_after)
    elif isinstance(context.error, BadRequest):
        logger.error(
            "Error while handling an update: ",
            exc_info=(BadRequest, context.error, None),
        )
    elif isinstance(context.error, TelegramError):
        logger.error(
            "Error while handling an update: ",
            exc_info=(TelegramError, context.error, None),
        )
    else:
        raise context.error
