from telegram.ext import CommandHandler, MessageHandler
from telegram.ext.filters import Regex

from src.commands.creating import create_voting, suggest_movie
from src.commands.getting import (
    change_watch_date,
    get_already_watched_movies_links,
    define_custom_movie_description,
    get_current_movies,
)
from src.commands.introducing import get_help


def get_all_handlers() -> list:
    handlers = [
        CommandHandler("help", get_help),
        CommandHandler("cd", change_watch_date, has_args=True),
        CommandHandler("already", get_already_watched_movies_links),
        CommandHandler(
            "custom", define_custom_movie_description, has_args=True
        ),
        CommandHandler("vote", create_voting),
        CommandHandler("now", get_current_movies),
        MessageHandler(
            Regex(r"^#предлагаю\s")
            & Regex(r"https://www.kinopoisk.ru/film/\d+/[\s|,]?"),
            suggest_movie,
        ),
    ]
    return handlers
