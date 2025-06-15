from concurrent.futures import ThreadPoolExecutor
from locale import setlocale, LC_ALL
from logging import getLogger
from datetime import datetime, timedelta
from math import ceil
from os import getcwd
from os.path import relpath

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegraph.exceptions import TelegraphException

from src.commands.creating import create_rating_voting
from src.config import Config
from src.db.services import (
    retrieve_current_session_movies,
    retrieve_already_watched_movies,
    delete_jobs,
    create_jobs,
)

from src.utils import (
    authentication,
    admin_only,
    generate_html,
    telegraph_init,
    process_movies_json,
)
from src.utils.kinopoisk import get_random_movie

logger = getLogger(__name__)


@admin_only
async def define_custom_movie_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    logger.info("Custom description added -> %s" % context.args)
    context.bot_data["custom"] = " ".join(context.args)
    return await update.message.reply_text("Добавил ваше описание!")


@admin_only
async def change_watch_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_string = context.args
    if len(date_string) > 1 or len(date_string[0]) > 5:
        logger.error("Invalid date format provided -> %s" % date_string)
        return await update.message.reply_text("Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05")
    year = datetime.now().year
    if "-" in date_string[0]:
        fmt = "%d-%m"
    elif ":" in date_string[0]:
        fmt = "%d:%m"
    elif "/" in date_string[0]:
        fmt = "%d/%m"
    else:
        logger.error("Invalid date format provided -> %s" % date_string)
        return await update.message.reply_text("Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05")
    try:
        logger.info("Changing locale on ru_Ru")
        setlocale(LC_ALL, "ru_RU.UTF-8")
        date = datetime.strptime(date_string[0], fmt).replace(year=year, hour=22, minute=00).isoformat()
        context.bot_data["date"] = date
        jobs = context.job_queue.get_jobs_by_name("rating")
        logger.info("Getting current session movies!")
        current_movies = await retrieve_current_session_movies()
        if jobs:
            logger.info("Deleting rating jobs")
            await delete_jobs("rating")
            for job in jobs:
                job[0].schedule_removal()
        job_date = datetime.fromisoformat(context.bot_data.get("date"))
        job_data = []
        for movie in current_movies:
            current_job_data = [
                "rating",
                create_rating_voting.__name__,
                relpath(__file__, getcwd()),
                job_date,
                context.bot_data["poll"]["id"],
                movie[1],
            ]
            context.job_queue.run_once(
                create_rating_voting,
                name="rating",
                when=job_date,
                chat_id=Config.GROUP_ID.value,
                data={
                    "poll_id": context.bot_data["poll"]["id"],
                    "movie": movie[1],
                },
            )
            job_date = job_date + timedelta(minutes=10)
            job_data.append(current_job_data)
        if job_data:
            logger.info("Re-creating all jobs")
            await create_jobs(job_data)
        return await update.message.reply_text(
            "Фильм перенесён!\nТекущая дата просмотра: %s" % datetime.fromisoformat(date).strftime("%A, %d-%m-%Y")
        )
    except ValueError:
        logger.error("Date parse error -> date_string -> %s -> format -> %s" % (date_string[0], fmt))
        return await update.message.reply_text("Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05")


@authentication
async def get_current_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    logger.info("Getting current session movies!")
    movies = await retrieve_current_session_movies()
    if not movies:
        logger.error("No movies found!")
        return await update.message.chat.send_message("Мы пока ничего не смотрим!")
    output = [
        f"""<b>{idx + 1}. Фильм: {item[1]}.</b>
<i>Жанры: {item[5]}.</i>
<i>Страны производства: {item[6]}.</i>
<i>Рейтинг IMDb: {item[7]}.</i>
<i>Режиссер: {item[0]}.</i>
<i>Год: {item[2]}.</i>
<i>Длительность в минутах: {item[3]}.</i>
<i>Предложен: {item[8]}.</i>
<i>Ссылка на кинопоиск: {item[4]}</i>
    """
        for idx, item in enumerate(movies)
    ]
    output.insert(0, "<b>#смотрим</b>")
    if context.chat_data.get("custom"):
        output.insert(0, context.bot_data["custom"])
    return await update.message.chat.send_message("\n".join(output), parse_mode=ParseMode.HTML)


async def get_already_watched_movies_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool | Message:
    logger.info("Initializing telegraph instance!")
    telegraph = await telegraph_init(context)
    urls = context.chat_data.get("urls")
    logger.info("Getting already watched movies!")
    movies = await retrieve_already_watched_movies()
    limit = 65
    length = ceil(len([*movies]) / limit)
    logger.info("Passing work to thread poll executor!")
    with ThreadPoolExecutor(max_workers=length) as executor:
        results = executor.submit(generate_html, movies)
    pages_data = results.result()
    if not urls:
        if not context.chat_data.get("msg"):
            logger.info("Creating telegraph pages!")
            new_pages = [
                (
                    await telegraph.create_page(
                        title="Список просмотренных фильмов",
                        html_content=pages_data[data],
                        author_name="КиноКлассБот",
                    )
                )["url"]
                for data in range(0, len(pages_data))
            ]
            context.chat_data["page_data"] = pages_data[-1]
            context.chat_data["urls"] = new_pages[-1]
            links = [f"{idx + 1}. {link}" for idx, link in enumerate(new_pages)]
            msg_id = context.chat_data.get("msg")
            if msg_id:
                await update.get_bot().delete_message(Config.GROUP_ID.value, msg_id)
            else:
                msg = await update.message.chat.send_message(text="\n".join(links))
                context.chat_data["msg"] = msg.id
            context.chat_data["all_msgs"] = links
            await update.get_bot().pin_chat_message(
                Config.GROUP_ID.value,
                update.message.id + 1,
                disable_notification=True,
            )
            return await update.get_bot().delete_message(
                chat_id=Config.GROUP_ID.value, message_id=update.message.id + 2
            )
        else:
            links = context.chat_data["all_msg"]
            logger.info("Creating extra telegraph page!")
            new_link = (
                await telegraph.create_page(
                    title="Список просмотренных фильмов",
                    html_content=pages_data[-1],
                    author_name="КиноКлассБот",
                )
            )["url"]
            links.append(f"{len(links) + 1}. {new_link}")
            context.chat_data["urls"] = new_link
            context.chat_data["all_msg"] = links
            return await update.get_bot().edit_message_text(links, Config.GROUP_ID.value, context.chat_data["msg"])
    else:
        url = context.chat_data["urls"]
        page_data = context.chat_data["page_data"]
        try:
            logger.info("Editing last telegraph page!")
            page = await telegraph.edit_page(
                path=url.split("/")[-1],
                title="Список просмотренных фильмов",
                html_content=page_data,
            )
        except TelegraphException as exc:
            logger.error("Telegraph exception occured -> %s" % exc)
            context.chat_data["urls"] = None
            logger.error("Recalling this function again!")
            return await get_already_watched_movies_links(update, context)
        msg_id = context.chat_data.get("msg")
        links = context.chat_data["all_msgs"]
        links.pop(-1)
        links.append(f"{len(links) + 1}. {page['url']}")
        context.chat_data["all_msg"] = links
        output = "\n".join(links)
        await update.get_bot().edit_message_text(
            text="%s\n%s" % (output, datetime.now().strftime("%m-%d-%Y %H:%M:%S")),
            chat_id=Config.GROUP_ID.value,
            message_id=msg_id,
        )


async def retrieve_random_movie_from_kinopoisk(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    logger.info("Getting random movie data from kinopoisk")
    random_movie = await get_random_movie()
    logger.info("Processing movie data from kinopoisk")
    serialized_movie = await process_movies_json([random_movie], update)
    output = f"""<b>Фильм: {serialized_movie[0][0]}.</b>
<i>Описание: {serialized_movie[0][1]}</i>
<i>Жанры: {serialized_movie[0][5]}.</i>
<i>Страны производства: {serialized_movie[0][4]}.</i>
<i>Рейтинг IMDb: {serialized_movie[0][8]}.</i>
<i>Режиссер: {serialized_movie[0][2]}.</i>
<i>Год: {serialized_movie[0][3]}.</i>
<i>Длительность в минутах: {serialized_movie[0][7]}.</i>
<i>Запрошен: {serialized_movie[0][9]}.</i>
<i>Ссылка на кинопоиск: {serialized_movie[0][6]}</i>
    """
    return await update.message.chat.send_message(text=output, parse_mode=ParseMode.HTML)
