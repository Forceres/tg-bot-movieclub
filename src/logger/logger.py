from logging import (
    basicConfig,
    getLogger,
    CRITICAL,
    FileHandler,
    StreamHandler,
    Formatter,
)
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from sys import stdout
from src.logger.formatter import CustomFormatter

load_dotenv()


def setup_logger():
    basicConfig(
        level=getenv("LEVEL"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M",
    )
    custom_formatter = CustomFormatter()
    default_formatter = Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M"
    )

    getLogger("httpx").setLevel(CRITICAL)
    getLogger("apscheduler").setLevel(CRITICAL)

    logger = getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = FileHandler(
        "{0}/{1}.log".format(
            "../logs", datetime.now().strftime("%Y-%m-%d %H-%M")
        )
    )
    file_handler.setFormatter(default_formatter)
    logger.addHandler(file_handler)

    terminal_handler = StreamHandler(stream=stdout)
    terminal_handler.setFormatter(custom_formatter)
    logger.addHandler(terminal_handler)
