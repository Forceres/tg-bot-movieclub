from enum import Enum
from os import getenv

from dotenv import load_dotenv

load_dotenv()


class Config(Enum):
    DATABASE = getenv("DATABASE")
    LOGGING_LEVEL = getenv("LEVEL")
    TOKEN = getenv("TOKEN")
