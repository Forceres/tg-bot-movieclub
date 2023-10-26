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
        bot = update.get_bot()
        admins = [
            admin.user.id
            for admin in await bot.get_chat_administrators(
                chat_id=Config.GROUP_ID.value
            )
        ]
    except TelegramError:
        logger.error(
            """Destination error -> there is no such a chat -> %s"""
            % Config.GROUP_ID.value
        )
        await update.message.reply_text("Нет такого чата!")
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
    func: Callable[[Update, Any], Coroutine[Any, Any, None]]
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def wrapper(update: Update, args: Any):
        if not await _check_if_in_group(update):
            return
        return await func(update, args)

    return wrapper


def admin_only(
    func: Callable[[Update, Any], Coroutine[Any, Any, None]]
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def wrapper(update: Update, args: Any):
        if not await _check_if_in_group(update) or not await _check_if_admin(
            update
        ):
            return
        return await func(update, args)

    return wrapper
