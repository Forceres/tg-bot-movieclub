from logging import getLogger

from telegram import CallbackQuery
from telegram.ext import ContextTypes

logger = getLogger(__name__)


async def process_callback_data(context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery) -> bool:
    (
        movies,
        offset,
        limit,
        movies_iterations,
        keyboard,
    ) = context.chat_data["suggested"]
    query_data = query.data
    match query_data:
        case "right":
            offset = offset + 10
        case "left":
            offset = offset - 10
    if offset < 0:
        offset = movies_iterations * 10 - 10
    elif movies_iterations * 10 <= offset:
        offset = 0
    context.chat_data["suggested"] = [
        movies,
        offset,
        limit,
        movies_iterations,
        keyboard,
    ]
    return True
