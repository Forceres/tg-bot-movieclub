from math import ceil
from random import choice

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.config import Config
from src.db.services import (
    suggest_new_movies,
    update_existed_movies,
    update_rating,
    assign_winner,
    check_if_movies_exist,
    create_new_voting,
    delete_voting,
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
    if context.chat_data.get("active_voting"):
        return await update.message.reply_text(
            "Голосование уже запущено!"
            "Нельзя создавать 2 голосования одновременно!"
        )
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

    if -1 in chosen_movie_numbers or len(chosen_movie_numbers) < 2:
        return

    movies = context.chat_data["suggested"][0]
    chosen_movies = [movies[number][1] for number in chosen_movie_numbers]

    await update.message.delete()
    context.chat_data["chosen_movie_ids"] = chosen_movie_numbers
    chosen_movies_ids = [
        movies[movie_id][0] for movie_id in chosen_movie_numbers
    ]
    await create_new_voting(chosen_movies_ids, context.chat_data["type"])
    context.chat_data["active_voting"] = True
    poll = await update.get_bot().send_poll(
        Config.GROUP_ID.value,
        "Что смотрим?",
        chosen_movies,
        is_anonymous=False,
        allows_multiple_answers=True,
        open_period=context.chat_data["duration"],
    )
    context.bot_data.update(
        {
            "poll": {
                "id": poll.id,
                "questions": chosen_movies,
                "type": context.chat_data["type"],
            }
        }
    )
    context.job_queue.run_once(
        process_voting_after_closing,
        when=context.chat_data["duration"],
        data=update.effective_chat.full_name,
        chat_id=update.message.chat_id,
    )
    return ConversationHandler.END


async def receive_voting_results(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not context.bot_data.get("answers"):
        context.bot_data["answers"] = {}
    poll = context.bot_data["poll"]
    questions = poll["questions"]
    answers = update.poll_answer.option_ids
    user_id = update.poll_answer.user.id
    chosen = [questions[answer] for answer in answers]
    if poll.get("type") != "schultze":
        results = {question: 0 for question in questions}
        for question in chosen:
            results[question] += 1
        results = {user_id: results}
    else:
        results = {user_id: chosen}
    context.bot_data["answers"].update(results)


async def process_voting_after_closing(context: ContextTypes.DEFAULT_TYPE):
    poll_type = context.bot_data["poll"].get("type")
    users_answers = context.bot_data["answers"]
    if poll_type != "schultze":
        questions = {
            question: 0 for question in context.bot_data["poll"]["questions"]
        }
        for user_answer in users_answers.values():
            for answer in user_answer:
                if user_answer[answer] == 1:
                    questions[answer] += 1

        await context.bot.delete_message(
            Config.GROUP_ID.value, context.bot_data["poll"]["id"]
        )
        if poll_type == "asc":
            winner_num = max(questions.items(), key=lambda item: item[1])[1]
        else:
            winner_num = min(questions.items(), key=lambda item: item[1])[1]
        winner_name = choice(
            [pair[0] for pair in questions.items() if pair[1] == winner_num]
        )
        winner = await assign_winner(winner_name)

        context.chat_data["active_voting"] = False
        context.bot_data["winner"] = winner_name
        context.bot_data["poll"].clear()
        context.bot_data["answers"].clear()
        context.job_queue.run_once(
            create_rating_voting,
            when=context.bot_data.get("date"),
            chat_id=Config.GROUP_ID.value,
        )
        if not winner:
            return await context.bot.send_message(
                Config.GROUP_ID.value, "Не удалось определить победителя!"
            )
        return await context.bot.send_message(
            Config.GROUP_ID.value, "Вызовите /now, чтобы увидеть победителя!"
        )
    else:
        questions = []
        for user_answer in users_answers.values():
            preferences = []
            for answer in user_answer:
                if user_answer[answer] == 1:
                    preferences.append(answer)
            questions.append(preferences)
        # TODO: IMPLEMENT SCHULTZE METHOD


async def create_rating_voting(context: ContextTypes.DEFAULT_TYPE):
    questions = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    rating_poll = await context.bot.send_poll(
        Config.GROUP_ID.value,
        f"Оцените фильм (от 1 до 10): {context.bot_data['winner']}",
        options=questions,
        is_anonymous=False,
        allows_multiple_answers=False,
        open_period=10,
    )
    rating_poll = {"poll": {"id": rating_poll.id, "questions": questions}}
    context.bot_data.update(rating_poll)
    context.job_queue.run_once(
        receive_rating_results,
        context.bot_data["date"],
        chat_id=Config.GROUP_ID.value,
    )
    return await context.bot.send_message(
        Config.GROUP_ID.value, str(context.bot_data["poll"])
    )


async def receive_rating_results(context: ContextTypes.DEFAULT_TYPE):
    answers = context.bot_data["answers"]
    rating = 0
    user_answers = answers.values()
    for user_answer in user_answers:
        for answer in user_answer:
            if user_answer[answer] == 1:
                rating += int(answer)
    rating /= len(user_answers)
    updated = await update_rating([rating, context.bot_data["winner"]])
    await context.bot.send_message(
        chat_id=Config.GROUP_ID.value,
        text="Фильм: %s, набрал %s" % (context.bot_data["winner"], rating),
    )
    await context.bot.delete_message(
        Config.GROUP_ID.value, context.bot_data["poll"]["id"]
    )
    if not updated:
        await context.bot.send_message(
            Config.GROUP_ID.value, "Произошла ошибка при обновлении рейтинга."
        )
    context.bot_data["poll"].clear()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["active_voting"] = False
    await update.message.delete()
    await update.get_bot().delete_message(
        Config.GROUP_ID.value, context.chat_data["message_id"]
    )
    return ConversationHandler.END


async def delete_current_voting(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    poll = context.bot_data.get("poll")
    if not poll:
        return await update.message.reply_text("Голосование не запущено!")
    deleted = await delete_voting()
    if deleted:
        await update.get_bot().delete_message(
            Config.GROUP_ID.value, poll["id"]
        )
        return await update.message.reply_text("Голосование удалено!")
    else:
        return await update.message.reply_text("Произошла ошибка!")


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
