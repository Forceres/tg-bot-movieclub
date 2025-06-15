from enum import Enum
from os import getenv

from dotenv import load_dotenv

env_file_name = getenv("ENV_FILE", ".env.dev")

load_dotenv(dotenv_path=env_file_name)


class Config(Enum):
    GROUP_ID = getenv("GROUP_ID")
    DATABASE = getenv("DATABASE")
    LOGGING_LEVEL = getenv("LEVEL")
    TOKEN = getenv("TOKEN")
    KINOPOISK_API_KEY = getenv("KINOPOISK_API_KEY")
    KINOPOISK_API_URL = getenv("KINOPOISK_API_URL")
    KINOPOISK_API_VERSION = getenv("KINOPOISK_API_VERSION")
