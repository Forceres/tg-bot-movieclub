from logging import (
    basicConfig,
    getLogger,
    FileHandler,
    StreamHandler,
    Formatter,
    WARNING,
)

from datetime import datetime
from sys import stdout
from os import listdir, mkdir

from src.logger.formatter import CustomFormatter
from src.config import Config


def setup_logger():
    basicConfig(
        level=Config.LOGGING_LEVEL.value,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M",
    )
    custom_formatter = CustomFormatter()
    default_formatter = Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M"
    )

    getLogger("httpx").setLevel(WARNING)
    getLogger("apscheduler").setLevel(WARNING)

    logger = getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()

    if "logs" not in listdir("."):
        mkdir("./logs")

    file_handler = FileHandler(
        "{0}/{1}.log".format(
            "./logs", datetime.now().strftime("%Y-%m-%d %H-%M")
        )
    )
    file_handler.setFormatter(default_formatter)
    logger.addHandler(file_handler)

    terminal_handler = StreamHandler(stream=stdout)
    terminal_handler.setFormatter(custom_formatter)
    logger.addHandler(terminal_handler)
