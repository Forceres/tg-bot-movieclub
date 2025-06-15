from datetime import datetime, timedelta
from math import ceil
from os import getcwd
from os.path import relpath
from random import choice
from re import match
from logging import getLogger

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.config import Config
from src.db.services import (
    update_rating_and_finish_watch,
    finish_session,
    add_movies_to_current_session,
    add_votes,
    delete_certain_votes,
    create_voter,
    retrieve_movies_with_min_votes,
    retrieve_current_voting_type,
    retrieve_movies_with_max_votes,
    assign_votes_after_voting,
    delete_all_votes,
    add_rating_vote,
    delete_certain_rating_votes,
    calculate_rating,
    delete_all_rating_votes_of_movie,
    suggest_new_movies,
    update_existed_movies,
    assign_winner,
    check_if_movies_exist,
    create_new_voting,
    delete_voting,
    create_jobs,
    delete_jobs,
    retrieve_suggested_movies,
    retrieve_current_session_movies,
    update_movie_rating,
    delete_movie_from_session,
)
from src.utils import (
    authentication,
    admin_only,
    parse_ids,
    parse_refs,
    process_callback_data,
    process_movies_json,
    get_relative_date,
    get_movies_data_from_kinopoisk,
)

logger = getLogger(__name__)


async def restart_rating_jobs(context: ContextTypes.DEFAULT_TYPE):
    current_movies = await retrieve_current_session_movies()
    previous_date = datetime.fromisoformat(context.bot_data.get("date"))
    if not previous_date or datetime.now().date() > previous_date.date():
        logger.info("Calculating relative date")
        await get_relative_date(context)
    if datetime.now().time() > previous_date.time() and datetime.now().date() == previous_date.date():
        logger.info("Calculating new date")
        context.bot_data["date"] = datetime.now() + timedelta(minutes=10)
    jobs = context.job_queue.get_jobs_by_name("rating")
    if jobs:
        logger.info("Deleting existing jobs")
        await delete_jobs("rating")
        for job in jobs:
            job.schedule_removal()
    date = datetime.fromisoformat(context.bot_data.get("date"))
    job_data = []
    for movie in current_movies:
        current_job_data = [
            "rating",
            create_rating_voting.__name__,
            relpath(__file__, getcwd()),
            date.isoformat(),
            context.job.data["poll_id"],
            movie[1],
        ]
        context.job_queue.run_once(
            create_rating_voting,
            when=date,
            chat_id=Config.GROUP_ID.value,
            name="rating",
            data={"poll_id": context.job.data["poll_id"], "movie": movie[1]},
        )
        date = date + timedelta(minutes=3)
        job_data.append(current_job_data)
    if job_data:
        logger.info("Creating new jobs")
        await create_jobs(job_data)


async def prepare_suggested_movies_for_output(
    context: ContextTypes.DEFAULT_TYPE,
):
    movies = await retrieve_suggested_movies()
    if not movies:
        logger.error("No movies")
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

    output = "\n".join([f"{offset + idx + 1}. {movie[1]}" for idx, movie in enumerate(movies[offset : limit + offset])])
    return output


async def send_prepared_output(output: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies, offset, limit, movies_iterations, keyboard = context.chat_data["suggested"]
    if len([*movies]) > limit:
        logger.info("Movies are exceeded the limit!")
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
        logger.info("Movies are in limit!")
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
        logger.error("There are no suggested movies!")
        return await update.message.chat.send_message("В предложке нет фильмов!")
    logger.info("Movies are about to be sent!")
    await send_prepared_output(output, update, context)
    return 1


async def process_integer_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_movie_numbers = {int(number.strip()) - 1 for number in update.message.text.split(",")}
    context.chat_data["chosen"] = chosen_movie_numbers
    if -1 in chosen_movie_numbers:
        logger.error("Answers validation failed!")
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
        logger.info("Added %s movies to current session" % len(chosen_movie_ids))
        await restart_rating_jobs(context)
        await update.message.chat.send_message("Добавил ваш(и) фильм(ы)!")
        return ConversationHandler.END
    else:
        logger.error("Chosen movies are already added to current session!")
        await update.message.chat.send_message("Фильм(ы) уже находятся в списке на 'просмотр'!")
        return ConversationHandler.END


async def cancel_add(_update: Update, _context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END


@admin_only
async def create_voting_type_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot_data.get("active_voting"):
        logger.error("Voting are already activated!")
        return await update.message.reply_text(
            "Голосование уже запущено!" "Нельзя создавать 2 голосования одновременно!"
        )
    await update.message.delete()
    keyboard = [
        [
            InlineKeyboardButton("Возрастающее", callback_data="asc"),
            InlineKeyboardButton("Убывающее", callback_data="desc"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    message_id = (await update.message.chat.send_message("Выбери тип голосования!", reply_markup=markup)).id
    context.chat_data["message_id"] = message_id
    return 1


async def base_settings_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ["asc", "desc"]:
        logger.info("Voting duration stage!")
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
        logger.info("Getting voting movies stage!")
        context.chat_data["duration"] = query.data
        output = await prepare_suggested_movies_for_output(context)
        if not output:
            logger.error("No suggested movies found!")
            await update.get_bot().send_message(text="В предложке нет фильмов!", chat_id=Config.GROUP_ID.value)
            return ConversationHandler.END
        await send_prepared_output(output, update, context)
        return 2


async def paginate_movies_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if context.chat_data.get("suggested"):
        logger.info("Suggested movies paginated!")
        if not await process_callback_data(context, query):
            return

        movies, offset, limit, movies_iterations, keyboard = context.chat_data["suggested"]

        output = "\n".join(
            [f"{offset + idx + 1}. {movie[1]}" for idx, movie in enumerate(movies[offset : limit + offset])]
        )
        await query.message.edit_text(output, reply_markup=InlineKeyboardMarkup(keyboard))


async def get_suggestions_and_create_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await process_integer_answers(update, context):
        return

    chosen_movie_numbers = context.chat_data["chosen"]

    movies = context.chat_data["suggested"][0]
    chosen_movies = [movies[number][1] for number in chosen_movie_numbers]

    await update.message.delete()
    context.chat_data["chosen_movie_ids"] = chosen_movie_numbers
    chosen_movies_ids = [movies[movie_id][0] for movie_id in chosen_movie_numbers]
    await create_new_voting(chosen_movies_ids, context.chat_data["type"])
    logger.info("Voting created!")
    context.bot_data["active_voting"] = True

    poll = await update.get_bot().send_poll(
        Config.GROUP_ID.value,
        "Что смотрим?",
        chosen_movies,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    logger.info("Poll %s sent!" % poll.id)
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
    date = datetime.now().replace(microsecond=0) + timedelta(seconds=duration)
    await update.get_bot().delete_message(Config.GROUP_ID.value, context.chat_data["message_id"])
    date = datetime.now() + timedelta(seconds=30)
    context.job_queue.run_once(
        process_voting_after_closing,
        when=date,
        data={"poll_id": poll.id},
        chat_id=update.message.chat_id,
        name="voting",
    )
    logger.info("Job - process_voting_after_closing -> on poll %s - successfully assigned!" % poll.id)
    await create_jobs(
        [
            "voting",
            process_voting_after_closing.__name__,
            relpath(__file__, getcwd()),
            date.isoformat(),
            poll.id,
            None,
        ]
    )
    return ConversationHandler.END


async def receive_voting_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.bot_data.get("voters"):
        logger.info("No voters found")
        context.bot_data["voters"] = []
    poll = context.bot_data["poll"]
    questions = poll["questions"]
    answers = update.poll_answer.option_ids
    user_id = update.poll_answer.user.id
    if user_id not in context.bot_data.get("voters"):
        logger.info("Voter creation -> %s" % user_id)
        await create_voter(user_id)
        context.bot_data["voters"].append(user_id)
    if poll.get("type"):
        logger.info("Voting poll entering -> %s" % poll.id)
        logger.info("Delete previous votes of %s" % user_id)
        await delete_certain_votes(user_id)
        chosen = [questions[answer] for answer in answers]
        results = {question: 0 for question in questions}
        for question in chosen:
            results[question] += 1
        results = {user_id: results}
        titles = []
        for movie in results[user_id]:
            if results[user_id].get(movie) == 1:
                titles.append(movie)
        logger.info("Votes adding -> %s <- %s" % (titles, user_id))
        await add_votes(titles, user_id)
    else:
        logger.info("Rating poll entering -> %s" % poll.id)
        rated = context.bot_data.get("rated")
        logger.info("Delete previous rating votes of %s" % user_id)
        await delete_certain_rating_votes(user_id)
        chosen_value = questions[answers[0]]
        logger.info("Rating votes adding -> %s -> %s -> %s" % (rated, user_id, chosen_value))
        await add_rating_vote(rated, user_id, chosen_value)


async def define_winner():
    logger.info("Getting poll type")
    poll_type = await retrieve_current_voting_type()
    if poll_type[0] == "asc":
        logger.info("Poll type is %s" % poll_type[0])
        winner_names = await retrieve_movies_with_max_votes()
    else:
        logger.info("Poll type is %s" % poll_type[0])
        winner_names = await retrieve_movies_with_min_votes()
    if not winner_names:
        logger.error("Winner were not defined!")
        return ""
    if len([*winner_names]) > 1:
        logger.info("Winner will be defined randomly!")
        return choice([winner_name[0] for winner_name in winner_names])
    else:
        winner = list(winner_names)[0][0]
        logger.info("Winner successfully defined -> %s" % winner)
        return winner


async def process_voting_after_closing(context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["active_voting"] = False
    await context.bot.delete_message(Config.GROUP_ID.value, context.job.data["poll_id"])
    logger.info("Defining winner...")
    winner_name = await define_winner()
    logger.info("Assigning votes after voting -> %s" % context.job.data["poll_id"])
    assigned = await assign_votes_after_voting()
    logger.info("Deleting all votes after voting -> %s" % context.job.data["poll_id"])
    await delete_all_votes()
    if not assigned:
        logger.error("Votes were not assigned -> %s" % winner_name)
        await context.bot.send_message(Config.GROUP_ID.value, "Произошла ошибка при назначении голосов!")
    context.bot_data["poll"].clear()
    logger.info("Deleting voting jobs")
    await delete_jobs("voting")
    if not winner_name:
        logger.error("Winner was not defined -> Deleting voting -> %s" % context.job.data["poll_id"])
        await delete_voting()
        return await context.bot.send_message(
            Config.GROUP_ID.value, "Не было получено ни одного голоса в ходе голосования!"
        )
    context.bot_data["winner"] = winner_name
    logger.info("Assigning winner -> %s" % winner_name)
    winner = await assign_winner(winner_name)
    context.bot_data["rated"] = winner_name
    if not winner:
        logger.error("Winner was not assigned -> %s" % winner_name)
        await context.bot.send_message(Config.GROUP_ID.value, "Не удалось определить победителя!")
    logger.info("Restarting rating jobs!")
    await restart_rating_jobs(context)
    return await context.bot.send_message(Config.GROUP_ID.value, "Вызовите /now, чтобы увидеть победителя!")


async def create_rating_voting(context: ContextTypes.DEFAULT_TYPE):
    questions = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    logger.info("Getting current session movies!")
    current_movies = await retrieve_current_session_movies()
    movies = []
    for movie in current_movies:
        movies.append(movie[1])
    context.bot_data["current_movies"] = movies
    current_movie = context.job.data["movie"]
    rating_poll = await context.bot.send_poll(
        Config.GROUP_ID.value,
        f"Оцените фильм (от 1 до 10): {current_movie}",
        options=questions,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    logger.info("Deleting rating jobs!")
    await delete_jobs("rating")
    date = datetime.now() + timedelta(minutes=3)
    context.job_queue.run_once(
        receive_rating_results,
        name="receive_rating",
        when=date,
        chat_id=Config.GROUP_ID.value,
        data={"poll_id": rating_poll.id, "movie": current_movie},
    )
    logger.info("Creating receive_rating jobs of %s" % current_movie)
    await create_jobs(
        [
            "receive_rating",
            receive_rating_results.__name__,
            relpath(__file__, getcwd()),
            date.isoformat(),
            rating_poll.id,
            current_movie,
        ]
    )
    rating_poll = {"poll": {"id": rating_poll.id, "questions": questions}}
    context.bot_data.update(rating_poll)


async def receive_rating_results(context: ContextTypes.DEFAULT_TYPE):
    to_be_rated = context.job.data["movie"]
    logger.info("Calculating rating for %s" % to_be_rated)
    rating = await calculate_rating(to_be_rated)
    logger.info("Deleting receive_rating jobs!")
    await delete_jobs("receive_rating")
    logger.info("Deleting all rating votes of %s" % to_be_rated)
    await delete_all_rating_votes_of_movie(to_be_rated)
    if not rating:
        logger.error("Rating calculation failed for %s" % to_be_rated)
        return await context.bot.send_message(Config.GROUP_ID.value, "Произошла ошибка при обновлении рейтинга.")
    logger.info("Updating rating for %s and set finish watch date" % to_be_rated)
    await update_rating_and_finish_watch([rating[0], to_be_rated])
    jobs = context.job_queue.get_jobs_by_name("rating")
    logger.info("Deleting receive_rating jobs!")
    await delete_jobs("receive_rating")
    if not jobs:
        logger.info("Closing current session!")
        await finish_session()
    await context.bot.send_message(
        chat_id=Config.GROUP_ID.value,
        text="Фильм: %s, набрал %s" % (to_be_rated, rating),
    )
    await context.bot.delete_message(Config.GROUP_ID.value, context.job.data["poll_id"])
    context.bot_data["poll"].clear()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Cancelling voting conversation handler!")
    context.bot_data["active_voting"] = False
    await update.message.delete()
    await update.get_bot().delete_message(Config.GROUP_ID.value, context.chat_data["message_id"])
    return ConversationHandler.END


async def cancel_current_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_active = context.bot_data.get("active_voting")
    if not is_active:
        logger.error("No active voting found!")
        return await update.message.reply_text("Голосование не запущено!")
    logger.info("Deleting active voting!")
    deleted = await delete_voting()
    job = context.job_queue.get_jobs_by_name("voting")
    context.bot_data["active_voting"] = False
    if job:
        logger.info("Deleting voting jobs!")
        job[0].schedule_removal()
        await delete_jobs("voting")
    if deleted:
        logger.info("Voting successfully deleted -> %s" % context.bot_data["poll"]["id"])
        await update.get_bot().delete_message(Config.GROUP_ID.value, context.bot_data["poll"]["id"])
        return await update.message.reply_text("Голосование отменено!")
    else:
        logger.error("Voting deletion failed -> %s" % context.bot_data["poll"]["id"])
        return await update.message.reply_text("Произошла ошибка при отмене голосования!")


@authentication
async def suggest_movie(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    logger.info("Parsing kinopoisk references: %s" % update.message.text)
    refs = await parse_refs(update.message.text)
    logger.info("Finding existed movies of %s" % refs)
    checked_refs = await check_if_movies_exist([*refs])
    if checked_refs:
        logger.info("Existed movies found, parsing its ids of %s" % checked_refs)
        checked_ids = await parse_ids(",".join([ref[0] for ref in checked_refs]))
        logger.info("Parsing base ids of %s" % update.message.text)
        base_ids = await parse_ids(update.message.text)
        ids = list(filter(lambda curr_id: curr_id not in checked_ids, base_ids))
        logger.info("Updating existed movies: %s" % checked_ids)
        update_state = await update_existed_movies([*checked_refs], update.effective_user.full_name)
        if len(ids) == 0 and update_state:
            logger.info("Existed movies were successfully updated!")
            return await update.message.reply_text("Вы обновили уже добавленные фильмы!")
        elif not update_state:
            logger.info("Existed movies update failed -> %s" % checked_refs)
            return await update.message.reply_text("Возникла ошибка с обновлением базы данных!")
    else:
        logger.info("Parsing new movies ids -> %s" % update.message.text)
        ids = await parse_ids(update.message.text)
    if len(ids) > 5:
        logger.error("Suggested more than 5 movies!")
        return await update.message.reply_text("Не предлагайте больше 5 фильмов за раз!")
    logger.info("Getting new movies data from kinopoisk for %s" % ids)
    responses = await get_movies_data_from_kinopoisk(ids)
    if not responses:
        logger.error("KinopoiskAPI returned no responses for %s" % ids)
        return await update.message.reply_text("Произошла ошибка со стороны KinopoiskAPI! Попробуйте позже!")
    logger.info("Processing new movies data!")
    movies = await process_movies_json(responses, update)
    logger.info("Adding new movies!")
    added = await suggest_new_movies(movies)
    if added:
        logger.info("New movies successfully added -> %s" % ids)
        return await update.message.reply_text("Ваше предложение было добавлено!")
    else:
        logger.error("New movies addition failed -> %s" % ids)
        return await update.message.reply_text("Произошла ошибка!")


async def forced_update_movie_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    pattern = r"https://www.kinopoisk.ru/film/\d+/(\?utm_referrer=\w+)"
    url_coincidence = match(pattern, args[0])
    if not (0 <= args[1] <= 10) or url_coincidence is None:
        logger.error("Invalid URL or mark: %s, %s" % (args[0], args[1]))
        return update.message.chat.send_message("Ссылка или оценка неправильны!")
    logger.info("Updating movie rating forcefully for %s - %s" % (args[0], args[1]))
    updated = await update_movie_rating(args[0], args[1])
    if not updated:
        logger.error("Error while forcefully updating movie rating for %s - %s" % (args[0], args[1]))
        return update.message.chat.send_message("Произошла ошибка при обновлении рейтинга!")
    logger.info("Movie rating successfully updated for %s - %s" % (args[0], args[1]))
    return update.message.chat.send_message("Рейтинг успешно обновлен!")


async def delete_movie_from_current_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = context.args
    pattern = r"https://www.kinopoisk.ru/film/\d+/(\?utm_referrer=\w+)"
    url_coincidence = match(pattern, link)
    if not url_coincidence:
        logger.error("Invalid URL provided -> %s" % link)
        return await update.message.chat.send_message("Передана неправильная ссылка!")
    logger.info("Deleting movie -> %s from current session" % link)
    deleted = await delete_movie_from_session(link)
    if not deleted:
        logger.error("Error while deleting movie -> %s from current session" % link)
        return await update.message.chat.send_message("Такого фильма нет в текущем сеансе!")
    logger.info("Movie successfully deleted from current session, restarting rating jobs!")
    await restart_rating_jobs(context)
