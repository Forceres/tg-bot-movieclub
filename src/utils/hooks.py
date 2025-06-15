from datetime import datetime, timedelta
from importlib import import_module
from logging import getLogger
from os import sep
from sqlite3 import Row
from typing import Iterable, Callable

from telegram.ext import Application
from telegraph.aio import Telegraph

from src.config import Config
from src.db.config import SqliteRepository
from src.utils import Queries

logger = getLogger(__name__)


async def startup(application: Application) -> None:
    logger.info("Starting up Bot!")
    await init_jobs(application)
    application.bot_data.update({"telegraph": Telegraph()})
    async with SqliteRepository() as db:
        await db.single_query(Queries.ENABLE_FOREIGN_KEYS.value)
    logger.info("Checking database connection!")
    if not SqliteRepository.check_connection():
        logger.error("Database connection failed!")
        await application.shutdown()


async def shutdown(application: Application) -> None:
    application.bot_data["telegraph"] = ""
    print(application.bot_data)
    await SqliteRepository.close()


async def get_all_jobs() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_ALL_JOBS.value)
        jobs = await cursor.fetchall()
        return jobs


async def init_jobs(application: Application) -> None:
    logger.info("Getting all jobs")
    jobs = await get_all_jobs()
    current_datetime = datetime.now()
    extra_time = 1
    for job in jobs:
        module_path = job[2].replace(sep, ".").replace(".py", "")
        func = import_func_from_module(module_path, job[1])
        if current_datetime > datetime.fromisoformat(job[3]):
            job_date = current_datetime + timedelta(minutes=extra_time)
        else:
            job_date = datetime.fromisoformat(job[3])
        application.job_queue.run_once(
            func,
            when=job_date,
            data={"poll_id": job[4], "movie": job[5]},
            name=job[0],
            chat_id=Config.GROUP_ID.value,
        )
        extra_time += 1


def import_func_from_module(module_path: str, func_name: str) -> Callable:
    logger.info("Importing function %s from %s" % (func_name, module_path))
    module = import_module(module_path)
    return getattr(module, func_name)


async def check_jobs(application: Application) -> None:
    print(application.job_queue.jobs())
