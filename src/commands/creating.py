from telegram import Update
from telegram.ext import ContextTypes

from src.db.services.creating import (
    suggest_new_movie,
    check_if_movies_exist,
    update_existed_movies,
)
from src.utils.authentication import authentication
from src.utils.convert_json_to_movie import process_movies_json
from src.utils.kinopoisk_api_call import api_call
from src.utils.parse_raw_string import parse_ids, parse_refs


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
    added = await suggest_new_movie(movies)
    if added:
        return await update.message.reply_text(
            "Ваше предложение было добавлено!"
        )
    else:
        return await update.message.reply_text("Произошла ошибка!")
