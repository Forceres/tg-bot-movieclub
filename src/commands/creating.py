import datetime
from math import ceil
from random import choice

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.config import Config
from src.db.services import (
    suggest_new_movies,
    update_existed_movies,
    assign_winner,
    check_if_movies_exist,
    create_new_voting,
    delete_voting,
)
from src.db.services.creating import (
    update_rating_and_finish_watch,
    finish_session, add_movies_to_current_session,
)
from src.db.services.getting import (
    retrieve_suggested_movies,
    retrieve_current_session_movies,
)
from src.utils.authentication import authentication, admin_only
from src.utils.callback_data_helpers import process_callback_data
from src.utils.convert_json_to_movie import process_movies_json
from src.utils.date_helper import get_relative_date
from src.utils.kinopoisk_api_call import api_call
from src.utils.parse_raw_string import parse_ids, parse_refs


async def prepare_suggested_movies_for_output(context: ContextTypes.DEFAULT_TYPE):
    movies = await retrieve_suggested_movies()
    if not movies:
        return False
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

    output = "\n".join(
        [
            f"{offset + idx + 1}. {movie[1]}"
            for idx, movie in enumerate(movies[offset: limit + offset])
        ]
    )
    return output


async def send_prepared_output(output: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies, offset, limit, movies_iterations, keyboard = context.chat_data[
        "suggested"
    ]
    if len([*movies]) > limit:
        markup = InlineKeyboardMarkup(keyboard)
        await update.get_bot().edit_message_text(
            "Выбери фильмы! "
            "P.S. передавай номера фильмов через запятую (минимум 2),"
            " 🤫🤫🤫 только никому не говори)\n%s" % output,
            chat_id=Config.GROUP_ID.value,
            message_id=context.chat_data["message_id"],
            reply_markup=markup,
        )
    else:
        await update.get_bot().edit_message_text(
            "Выбери фильмы! "
            "P.S. передавай номера фильмов через запятую (минимум 2),"
            " 🤫🤫🤫 только никому не говори)\n%s" % output,
            chat_id=Config.GROUP_ID.value,
            message_id=context.chat_data["message_id"],
        )


async def add_movie_to_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()
    context.chat_data["message_id"] = (await update.message.chat.send_message("Подожди секунду")).id
    output = await prepare_suggested_movies_for_output(context)
    if not output:
        return await update.message.chat.send_message(
            "В предложке нет фильмов!"
        )
    await send_prepared_output(output, update, context)
    return 1


async def process_integer_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_movie_numbers = {
        int(number.strip()) - 1 for number in update.message.text.split(",")
    }
    context.chat_data["chosen"] = chosen_movie_numbers
    if -1 in chosen_movie_numbers:
        return False
    return True


async def retrieve_chosen_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await process_integer_answers(update, context):
        return
    chosen_movie_numbers = context.chat_data["chosen"]
    movies = context.chat_data["suggested"][0]
    chosen_movie_ids = [movies[number][0] for number in chosen_movie_numbers]
    added = await add_movies_to_current_session(chosen_movie_ids)
    if added:
        await update.message.chat.send_message("Добавил ваш(и) фильм(ы)!")
        return ConversationHandler.END


async def cancel_add(_update: Update, _context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END


@admin_only
async def create_voting_type_keyboard(
        update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if context.chat_data.get("active_voting"):
        return await update.message.reply_text(
            "Голосование уже запущено!"
            "Нельзя создавать 2 голосования одновременно!"
        )
    await update.message.delete()
    keyboard = [
        [
            InlineKeyboardButton("Возрастающее", callback_data="asc"),
            InlineKeyboardButton("Убывающее", callback_data="desc"),
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
    if query.data in ["asc", "desc"]:
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
        output = await prepare_suggested_movies_for_output(context)
        if not output:
            return await update.message.chat.send_message(
                "В предложке нет фильмов!"
            )
        await send_prepared_output(output, update, context)
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
                for idx, movie in enumerate(movies[offset: limit + offset])
            ]
        )
        await query.message.edit_text(
            output, reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def get_suggestions_and_create_voting(
        update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not await process_integer_answers(update, context):
        return

    chosen_movie_numbers = context.chat_data["chosen"]

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
    duration = int(context.chat_data["duration"])
    await update.get_bot().delete_message(
        Config.GROUP_ID.value, context.chat_data["message_id"]
    )
    context.job_queue.run_once(
        process_voting_after_closing,
        when=duration,
        data=update.effective_chat.full_name,
        chat_id=update.message.chat_id,
        name="voting",
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
    results = {question: 0 for question in questions}
    if poll.get("type"):
        for question in chosen:
            results[question] += 1
        results = {user_id: results}
        context.bot_data["answers"].update(results)


async def define_winner(context: ContextTypes.DEFAULT_TYPE):
    poll_type = context.bot_data["poll"].get("type")
    users_answers = context.bot_data.get("answers")
    questions = {
        question: 0 for question in context.bot_data["poll"]["questions"]
    }
    for user_answer in users_answers.values():
        for answer in user_answer:
            if user_answer[answer] == 1:
                questions[answer] += 1
    if poll_type == "asc":
        winner_num = max(questions.items(), key=lambda item: item[1])[1]
    else:
        winner_num = min(questions.items(), key=lambda item: item[1])[1]
    winner_name = choice(
        [pair[0] for pair in questions.items() if pair[1] == winner_num]
    )
    return winner_name


async def process_voting_after_closing(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        Config.GROUP_ID.value, context.bot_data["poll"]["id"]
    )
    winner_name = await define_winner(context)
    winner = await assign_winner(winner_name)

    context.chat_data["active_voting"] = False
    context.bot_data["winner"] = winner_name
    context.bot_data["poll"].clear()
    context.bot_data["answers"].clear()

    current_movies = await retrieve_current_session_movies()

    await get_relative_date(context)

    jobs = context.job_queue.get_jobs_by_name("rating")

    if jobs:
        for job in jobs:
            job.schedule_removal()

    date = datetime.datetime.fromisoformat(context.bot_data.get("date"))
    for _ in current_movies:
        context.job_queue.run_once(
            create_rating_voting,
            when=date,
            chat_id=Config.GROUP_ID.value,
            name="rating",
        )
        date = date + datetime.timedelta(minutes=10)
    if not winner:
        return await context.bot.send_message(
            Config.GROUP_ID.value, "Не удалось определить победителя!"
        )
    return await context.bot.send_message(
        Config.GROUP_ID.value, "Вызовите /now, чтобы увидеть победителя!"
    )


async def create_rating_voting(context: ContextTypes.DEFAULT_TYPE):
    questions = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    current_movies = await retrieve_current_session_movies()
    movies = []
    for movie in range(len(*current_movies)):
        movies.append(movie)
    context.bot_data["current_movies"] = movies
    current_movie = movies[0]
    rating_poll = await context.bot.send_poll(
        Config.GROUP_ID.value,
        f"Оцените фильм (от 1 до 10): {current_movie}",
        options=questions,
        is_anonymous=False,
        allows_multiple_answers=False,
        open_period=600,
    )

    context.bot_data["rated"] = current_movie

    context.job_queue.run_once(
        receive_rating_results,
        datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        chat_id=Config.GROUP_ID.value,
    )
    rating_poll = {"poll": {"id": rating_poll.id, "questions": questions}}
    context.bot_data.update(rating_poll)
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
    updated = await update_rating_and_finish_watch(
        [rating, context.bot_data["rated"]]
    )
    jobs = context.job_queue.get_jobs_by_name("rating")
    if not jobs:
        await finish_session()
    await context.bot.send_message(
        chat_id=Config.GROUP_ID.value,
        text="Фильм: %s, набрал %s" % (context.bot_data["rated"], rating),
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


async def cancel_current_voting(
        update: Update, context: ContextTypes.DEFAULT_TYPE
):
    poll = context.bot_data.get("poll")
    if not poll:
        return await update.message.reply_text("Голосование не запущено!")
    deleted = await delete_voting()
    job = context.job_queue.get_jobs_by_name("voting")
    context.chat_data["active_voting"] = False
    if job:
        job[0].schedule_removal()
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
