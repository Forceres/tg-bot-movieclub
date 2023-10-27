from math import ceil

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.config import Config
from src.db.services.creating import (
    suggest_new_movies,
    check_if_movies_exist,
    update_existed_movies,
    create_new_voting,
)
from src.db.services.getting import retrieve_suggested_movies
from src.utils.authentication import authentication, admin_only
from src.utils.callback_data_helpers import process_callback_data
from src.utils.convert_json_to_movie import process_movies_json
from src.utils.kinopoisk_api_call import api_call
from src.utils.parse_raw_string import parse_ids, parse_refs


@admin_only
async def create_voting_type_keyboard(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.message.delete()
    keyboard = [
        [
            InlineKeyboardButton("Максимум", callback_data="asc"),
            InlineKeyboardButton("Минимум", callback_data="desc"),
            InlineKeyboardButton("Шульце", callback_data="schultze"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    message_id = (
        await update.message.chat.send_message(
            "Выбери тип голосования!", reply_markup=markup
        )
    ).id
    context.chat_data["message_id"] = message_id
    return 1


async def base_settings_button_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    if query.data in ["asc", "desc", "schultze"]:
        context.chat_data["type"] = query.data
        keyboard = [
            [
                InlineKeyboardButton("1 час", callback_data="3600"),
                InlineKeyboardButton("3 часа", callback_data="10800"),
                InlineKeyboardButton("1 день", callback_data="86400"),
                InlineKeyboardButton("3 дня", callback_data="259200"),
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.get_bot().edit_message_text(
            "Выбери длительность голосования!",
            Config.GROUP_ID.value,
            context.chat_data["message_id"],
            reply_markup=markup,
        )
    else:
        context.chat_data["duration"] = query.data
        movies = await retrieve_suggested_movies()
        if not movies:
            return await update.message.chat.send_message(
                "В предложке нет фильмов!"
            )
        offset = 0
        limit = 10
        movies_iterations = ceil(len([*movies]) / limit)
        keyboard = [
            [
                InlineKeyboardButton("<", callback_data="left"),
                InlineKeyboardButton(">", callback_data="right"),
            ]
        ]

        context.chat_data["suggested"] = [
            movies,
            offset,
            limit,
            movies_iterations,
            keyboard,
        ]

        markup = InlineKeyboardMarkup(keyboard)
        output = "\n".join(
            [
                f"{offset + idx + 1}. {movie[1]}"
                for idx, movie in enumerate(movies[offset : limit + offset])
            ]
        )
        await update.get_bot().edit_message_text(
            "Выбери фильмы!\n%s" % output,
            chat_id=Config.GROUP_ID.value,
            message_id=context.chat_data["message_id"],
            reply_markup=markup,
        )
        return 2


async def paginate_movies_button_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    if context.chat_data.get("suggested"):
        if not await process_callback_data(context, query):
            await update.message.chat.send_message("Ошибка!")

        movies, offset, limit, movies_iterations, keyboard = context.chat_data[
            "suggested"
        ]

        output = "\n".join(
            [
                f"{offset + idx + 1}. {movie[1]}"
                for idx, movie in enumerate(movies[offset : limit + offset])
            ]
        )
        await query.message.edit_text(
            output, reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def get_suggestions_and_create_voting(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    chosen_movie_numbers = {
        int(number.strip()) - 1 for number in update.message.text.split(",")
    }
    movies = context.chat_data["suggested"][0]
    chosen_movies = "\n".join(
        [movies[number][1] for number in chosen_movie_numbers]
    )
    await update.get_bot().edit_message_text(
        "Следующие фильмы добавлены в голосование:\n%s" % chosen_movies,
        Config.GROUP_ID.value,
        context.chat_data["message_id"],
    )
    await update.message.delete()
    context.chat_data["chosen_movie_ids"] = chosen_movie_numbers
    chosen_movies_ids = [
        movies[movie_id][0] for movie_id in chosen_movie_numbers
    ]
    await create_new_voting(chosen_movies_ids, context.chat_data["type"])
    poll = await update.get_bot().send_poll(
        Config.GROUP_ID.value,
        "Что смотрим?",
        chosen_movies.split("\n"),
        is_anonymous=False,
        allows_multiple_answers=True,
        open_period=30,
    )
    context.chat_data["poll"] = poll.id
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()
    await update.get_bot().delete_message(
        Config.GROUP_ID.value, context.chat_data["message_id"]
    )
    return ConversationHandler.END


@authentication
async def suggest_movie(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    refs = await parse_refs(update.message.text)
    checked_refs = await check_if_movies_exist([*refs])
    if checked_refs:
        checked_ids = await parse_ids(",".join(*checked_refs))
        base_ids = await parse_ids(update.message.text)
        ids = list(
            filter(lambda curr_id: curr_id not in checked_ids, base_ids)
        )
        update_state = await update_existed_movies(
            [*checked_refs], update.effective_user.full_name
        )
        if len(ids) == 0 and update_state:
            return await update.message.reply_text(
                "Вы обновили уже добавленные фильмы!"
            )
        elif not update_state:
            return await update.message.reply_text(
                "Возникла ошибка с обновлением базы данных!"
            )
    else:
        ids = await parse_ids(update.message.text)
    if len(ids) > 5:
        return await update.message.reply_text(
            "Не предлагайте больше 5 фильмов за раз!"
        )
    responses = await api_call(ids)
    if not responses:
        return await update.message.reply_text(
            "Произошла ошибка со стороны KinopoiskAPI! Попробуйте позже!"
        )
    movies = await process_movies_json(responses, update)
    added = await suggest_new_movies(movies)
    if added:
        return await update.message.reply_text(
            "Ваше предложение было добавлено!"
        )
    else:
        return await update.message.reply_text("Произошла ошибка!")
