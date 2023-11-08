from locale import setlocale, LC_ALL
from logging import getLogger
from datetime import datetime, timedelta

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegraph.exceptions import TelegraphException

from src.commands.creating import create_rating_voting
from src.config import Config
from src.db.services import (
    retrieve_current_session_movies,
    retrieve_already_watched_movies,
)

from src.utils.authentication import authentication, admin_only
from src.utils.generate_paginated_html import generate_html
from src.utils.telegraph_init import telegraph_init

logger = getLogger(__name__)


@admin_only
async def define_custom_movie_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Message:
    context.chat_data["custom"] = " ".join(context.args)
    return await update.message.reply_text("Добавил ваше описание!")


@admin_only
async def change_watch_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    date_string = context.args
    if len(date_string) > 1 or len(date_string[0]) > 5:
        return await update.message.reply_text(
            "Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05"
        )
    year = datetime.now().year
    if "-" in date_string[0]:
        fmt = "%d-%m"
    elif ":" in date_string[0]:
        fmt = "%d:%m"
    elif "/" in date_string[0]:
        fmt = "%d/%m"
    else:
        return await update.message.reply_text(
            "Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05"
        )
    try:
        setlocale(LC_ALL, "ru_RU.UTF-8")
        date = (
            datetime.strptime(date_string[0], fmt)
            .replace(year=year, hour=22, minute=00)
            .isoformat()
        )
        context.bot_data["date"] = date
        jobs = context.job_queue.get_jobs_by_name("rating")
        current_movies = await retrieve_current_session_movies()
        if jobs:
            for job in jobs:
                job[0].schedule_removal()
        job_date = datetime.fromisoformat(context.bot_data.get("date"))
        for _ in current_movies:
            context.job_queue.run_once(
                create_rating_voting,
                when=job_date,
                chat_id=Config.GROUP_ID.value,
                name="rating",
            )
            job_date = job_date + timedelta(minutes=10)
        return await update.message.reply_text(
            "Фильм перенесён!\nТекущая дата просмотра: %s"
            % datetime.fromisoformat(date).strftime("%A, %d-%m-%Y")
        )
    except ValueError:
        logger.error(
            "Date parse error -> date_string -> %s -> format -> %s"
            % (date_string[0], fmt)
        )
        return await update.message.reply_text(
            "Некорректный формат, передайте день(/,:,-)месяц, н-р, 03/05"
        )


@authentication
async def get_current_movies(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Message:
    movies = await retrieve_current_session_movies()
    if not movies:
        return await update.message.chat.send_message(
            "Мы пока ничего не смотрим!"
        )
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
        output.insert(0, context.chat_data["custom"])
    return await update.message.chat.send_message(
        "\n".join(output), parse_mode=ParseMode.HTML
    )


async def get_already_watched_movies_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool | Message:
    telegraph = await telegraph_init(context)
    urls = context.chat_data.get("urls")
    movies = await retrieve_already_watched_movies()
    pages_data = await generate_html(movies)
    if not urls:
        if not context.chat_data.get("msg"):
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
            links = [
                f"{idx + 1}. {link}" for idx, link in enumerate(new_pages)
            ]
            msg_id = context.chat_data.get("msg")
            if msg_id:
                await update.get_bot().delete_message(
                    Config.GROUP_ID.value, msg_id
                )
            else:
                msg = await update.message.chat.send_message(
                    text="\n".join(links)
                )
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
            return await update.get_bot().edit_message_text(
                links, Config.GROUP_ID.value, context.chat_data["msg"]
            )
    else:
        url = context.chat_data["urls"]
        page_data = context.chat_data["page_data"]
        try:
            page = await telegraph.edit_page(
                path=url.split("/")[-1],
                title="Список просмотренных фильмов",
                html_content=page_data,
            )
        except TelegraphException as exc:
            logger.error(exc)
            context.chat_data["urls"] = None
            return await get_already_watched_movies_links(update, context)
        msg_id = context.chat_data.get("msg")
        links = context.chat_data["all_msgs"]
        links.pop(-1)
        links.append(f"{len(links) + 1}. {page['url']}")
        context.chat_data["all_msg"] = links
        links.append(datetime.utcnow().strftime("%m-%d-%Y %H:%M:%S"))
        await update.get_bot().edit_message_text(
            text="\n".join(links),
            chat_id=Config.GROUP_ID.value,
            message_id=msg_id,
        )
