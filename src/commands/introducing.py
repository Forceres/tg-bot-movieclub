from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.utils.authentication import authentication


@authentication
async def get_help(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    message = r"""*Приветствую вас\! Это справка о командах бота\.*
_Добавить фильм в предложку можно с помощью отправки сообщения такого вида:_
_*\#предлагаю*_ https://www\.kinopoisk\.ru/film/здесь\-указан\-id\-фильма/
_Если хотите предложить несколько фильмов,
тогда располагайте ссылки через запятую или пробелы\!_
_В случае, если была передана ссылка на фильм,
который уже был просмотрен ранее, тогда он будет внесен в предложку,
то есть, его дата предложения изменится на текущую\!_
Список возможных команд:
/now \- вывести список фильмов текущего сеанса
/cd \- перенести дату обсуждения фильма
/help \- вывести справку о командах
/custom \- добавить свое произвольное описание к фильмам
/cancel_voting \- отменить голосование
/cancel \- РАБОТАЕТ ТОЛЬКО ВО ВРЕМЯ СОЗДАНИЯ ГОЛОСОВАНИЯ
/already \- получить ссылки с списком просмотренных фильмов
/vote \- создать голосование \(только администратор\)
    """
    return await update.message.chat.send_message(
        message, parse_mode=ParseMode.MARKDOWN_V2
    )
