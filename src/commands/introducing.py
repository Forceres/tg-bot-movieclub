from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.utils import authentication


logger = getLogger(__name__)


@authentication
async def get_help(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending help message!")
    message = r"""*Приветствую вас\! Это справка о командах бота\.*
_Добавить фильм в предложку можно с помощью отправки сообщения такого вида:_
_*\#предлагаю*_ https://www\.kinopoisk\.ru/film/здесь\-указан\-id\-фильма/_
Если хотите предложить несколько фильмов,
тогда располагайте ссылки через запятую или пробелы\!
В случае, если была передана ссылка на фильм,
который уже был просмотрен ранее, тогда он будет внесен в предложку, то есть, его дата предложения изменится
на текущую\!
Если указано arg около команды \- тогда нужно передавать с командой текст,
н\-р, /cd 12\-04, /del\_movie\_from\_session ссылка\-на\-кинопоиск, /custom описание,
/rating ссылка\-на\-кинопоиск оценка\-фильму\._
*Список возможных команд:*
/now \- вывести список фильмов текущего сеанса
/cd \- перенести дату обсуждения фильма \(только админ\) \(arg\)
/del\_movie\_from\_session \- удалить фильм из текущего сеанса \(только админ\) \(arg\)
/rating \- принудительно назначить рейтинг фильму \(только админ\) \(arg\)
/help \- вывести справку о командах
/custom \- добавить свое произвольное описание к фильмам \(arg\)
/cancel\_voting \- отменить голосование
/cancel \- РАБОТАЕТ ТОЛЬКО ВО ВРЕМЯ СОЗДАНИЯ ГОЛОСОВАНИЯ
/random \- получить случайный фильм из кинопоиска
/already \- получить ссылки со списком просмотренных фильмов
/vote \- создать голосование \(только админ\)
/adds \- добавить фильм без голосования \(только админ\)
    """
    return await update.message.chat.send_message(message, parse_mode=ParseMode.MARKDOWN_V2)
