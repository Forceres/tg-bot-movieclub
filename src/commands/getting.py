from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes

from src.db.services.getting import retrieve_current_session_movies
from src.utils.authentication import authentication

logger = getLogger(__name__)


@authentication
async def get_current_movies(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
):
    response = await retrieve_current_session_movies()
    output = [
        f"""{idx + 1}. Режиссер: {item[0]}.
    Фильм: {item[1]}.
    Год: {item[2]}.
    Длительность в минутах: {item[3]}
    Ссылка на кинопоиск: {item[4]}
    """
        for idx, item in enumerate(response)
    ]
    return await update.message.chat.send_message("\n".join(output))
