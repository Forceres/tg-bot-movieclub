from logging import Formatter, LogRecord
from colorama import Fore, init

init(autoreset=True)


class CustomFormatter(Formatter):
    COLOURS = {
        "CRITICAL": Fore.RED,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
        "INFO": Fore.GREEN,
        "DEBUG": Fore.RED,
    }

    def __init__(self):
        super().__init__(
            "%(asctime)s %(name)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M"
        )

    def format(self, record: LogRecord) -> str:
        color = self.COLOURS.get(record.levelname, "")
        if color:
            record.name = color + record.name
            record.levelname = color + record.levelname
            record.msg = color + record.msg
        return super().format(record)
