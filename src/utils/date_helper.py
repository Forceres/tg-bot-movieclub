from datetime import datetime, timedelta

from telegram.ext import ContextTypes


async def get_relative_date(context: ContextTypes.DEFAULT_TYPE):
    current_datetime = datetime.now().replace(microsecond=0)
    weekday = datetime.weekday(datetime.now())
    date = ""
    if weekday == 3:
        date = datetime.isoformat(
            (timedelta(7) + current_datetime).replace(hour=22, minute=0)
        )
    elif weekday < 3:
        date = datetime.isoformat(
            (timedelta(3 - weekday) + current_datetime).replace(
                hour=22, minute=0
            )
        )
    elif weekday > 3:
        date = datetime.isoformat(
            (timedelta(7 - (weekday - 3)) + current_datetime).replace(
                hour=22, minute=0
            )
        )
    context.bot_data["date"] = date
