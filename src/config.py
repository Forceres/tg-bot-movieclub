from enum import Enum
from os import getenv

from dotenv import load_dotenv

load_dotenv(getenv("ENV_FILE"))


class Config(Enum):
    DATABASE = getenv("DATABASE")
    LOGGING_LEVEL = getenv("LEVEL")
    TOKEN = getenv("TOKEN")
