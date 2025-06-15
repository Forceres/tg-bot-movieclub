from src.utils.authentication import authentication, admin_only
from src.utils.callback_data_helpers import process_callback_data
from src.utils.error_handler import error_handler
from src.utils.convert_json_to_movie import process_movies_json
from src.utils.date_helper import get_relative_date
from src.utils.queries import Queries
from src.utils.parse_raw_string import parse_ids, parse_refs
from src.utils.generate_paginated_html import generate_html
from src.utils.hooks import startup, shutdown
from src.utils.kinopoisk import get_movies_data_from_kinopoisk
from src.utils.movie_dto import Movie
from src.utils.telegraph_init import telegraph_init

__all__ = [
    "authentication",
    "admin_only",
    "process_callback_data",
    "process_movies_json",
    "get_relative_date",
    "parse_ids",
    "parse_refs",
    "generate_html",
    "telegraph_init",
    "error_handler",
    "get_movies_data_from_kinopoisk",
    "Movie",
    "shutdown",
    "startup",
    "Queries",
]
