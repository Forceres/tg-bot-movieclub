from logging import getLogger

from telegram import CallbackQuery
from telegram.ext import ContextTypes

logger = getLogger(__name__)


async def process_callback_data(
    context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
) -> bool:
    (
        movies,
        offset,
        limit,
        current_iteration,
        movies_iterations,
        keyboard,
    ) = context.chat_data["watched"]
    query_data = query.data
    match query_data:
        case ">":
            offset = offset + 30
            current_iteration += 1
        case "<":
            offset = offset - 30
            current_iteration -= 1
        case "0":
            return False
        case _:
            return not await query.delete_message()
    if offset < 0:
        offset = movies_iterations * 30 - 30
        current_iteration = movies_iterations
    elif movies_iterations * 30 <= offset:
        offset = 0
        current_iteration = 1
    context.chat_data["watched"] = [
        movies,
        offset,
        limit,
        current_iteration,
        movies_iterations,
        keyboard,
    ]
    return True
