from logging import getLogger
from typing import Coroutine, Callable, Any

from telegram import Update
from telegram.error import TelegramError

from src.config import Config

logger = getLogger(__name__)


async def _check_if_in_group(update: Update) -> bool | None:
    try:
        bot = update.get_bot()
        await bot.get_chat_member(
            chat_id=Config.GROUP_ID.value, user_id=update.effective_user.id
        )
    except TelegramError:
        logger.error(
            "Authentication error -> %s is not a KINOCLASS member"
            % update.effective_user.id
        )
        await update.message.reply_text("Вы не являетесь членом кинокласса!")
        return False
    else:
        return True


async def _check_if_admin(update: Update) -> bool | None:
    try:
        admins = [
            admin.user.id
            for admin in await update.message.chat.get_administrators()
        ]
    except TelegramError:
        logger.error(
            """Destination error -> you can't invoke this command
            in the private chat"""
        )
        await update.message.reply_text(
            "Вы не можете вызвать эту команду в личном чате!"
        )
    else:
        if update.effective_user.id not in admins:
            logger.error(
                "Authentication error -> %s is not an administrator"
                % update.effective_user.id
            )
            await update.message.reply_text("Вы не являетесь администратором!")
            return False
        return True


def authentication(
    func: Callable,
) -> Callable[[tuple[Any, ...]], Coroutine[Any, Any, None]]:
    async def wrapper(*args):
        if not await _check_if_in_group(args[0]):
            return
        await func(*args)

    return wrapper


def admin_only(
    func: Callable,
) -> Callable[[tuple[Any, ...]], Coroutine[Any, Any, None]]:
    async def wrapper(*args):
        if not await _check_if_in_group(args[0]) or not await _check_if_admin(
            args[0]
        ):
            return
        await func(*args)

    return wrapper
