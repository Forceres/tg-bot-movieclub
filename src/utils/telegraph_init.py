from logging import getLogger

from telegram.ext import ContextTypes
from telegraph.aio import Telegraph
from telegraph.exceptions import TelegraphException

logger = getLogger(__name__)


async def telegraph_init(context: ContextTypes.DEFAULT_TYPE) -> Telegraph:
    telegraph: Telegraph = context.bot_data["telegraph"]
    info = ""
    try:
        info = await telegraph.get_account_info()
    except TelegraphException:
        logger.warning("Account already exists")
    if not info:
        await telegraph.create_account(short_name="KinoClassBot")
    return telegraph
