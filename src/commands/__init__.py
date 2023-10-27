from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.ext.filters import Regex

from src.commands.creating import (
    suggest_movie,
    create_voting_type_keyboard,
    base_settings_button_callback,
    paginate_movies_button_callback,
    get_suggestions_and_create_voting,
    cancel,
)
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
        CommandHandler("now", get_current_movies),
        MessageHandler(
            Regex(r"^#предлагаю\s")
            & Regex(r"https://www.kinopoisk.ru/film/\d+/[\s|,]?"),
            suggest_movie,
        ),
        ConversationHandler(
            entry_points=[CommandHandler("vote", create_voting_type_keyboard)],
            states={
                1: [CallbackQueryHandler(base_settings_button_callback)],
                2: [
                    CallbackQueryHandler(paginate_movies_button_callback),
                    MessageHandler(
                        Regex(r"(\d{1,3}(?:,\s*\d{1,3})(?![\d\s|[\w|\W]))")
                        | Regex(r"(^\d{1,3}$)"),
                        get_suggestions_and_create_voting,
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
    ]
    return handlers
