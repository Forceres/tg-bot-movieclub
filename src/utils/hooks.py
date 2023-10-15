import logging

from telegram.ext import Application

from src.db.config.db import SqliteRepository
from src.utils.queries import Queries


async def startup(application: Application) -> None:
    logging.info("Starting up Bot!")
    async with SqliteRepository() as db:
        await db.single_query(Queries.ENABLE_FOREIGN_KEYS.value)
    if not SqliteRepository.check_connection():
        await application.shutdown()


async def shutdown(_application: Application) -> None:
    await SqliteRepository.close()
