import logging

from telegram.ext import Application

from src.db.config.db import SqliteRepository


async def startup(application: Application) -> None:
    logging.info("Starting up Bot!")
    await (await SqliteRepository()).close_cursor()
    if not SqliteRepository.check_connection():
        await application.shutdown()


async def shutdown(_application: Application) -> None:
    await SqliteRepository.close()
