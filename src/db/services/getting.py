from logging import getLogger
from sqlite3 import Row
from typing import Iterable

from aiosqlite import Cursor

from src.db.config.db import SqliteRepository
from src.utils.queries import Queries

logger = getLogger(__name__)


async def retrieve_current_session_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        result: Cursor = await db.single_query(
            Queries.GET_CURRENT_MOVIES.value
        )
        output: Iterable[Row] = await result.fetchall()
        logger.warning(
            "Query completed! -> {}".format(Queries.GET_CURRENT_MOVIES.value)
        )
    return output


async def retrieve_suggested_movies() -> Iterable[Row] | bool:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(
            Queries.GET_SUGGESTED_MOVIES.value
        )
        if cursor is None:
            return False
        output: Iterable[Row] = await cursor.fetchall()
        logger.warning(
            "Query completed! -> {}".format(Queries.GET_SUGGESTED_MOVIES.value)
        )
    return output


async def retrieve_already_watched_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        result: Cursor = await db.single_query(
            Queries.GET_ALREADY_WATCHED_MOVIES.value
        )
        output: Iterable[Row] = await result.fetchall()
        logger.warning(
            "Query completed! -> {}".format(
                Queries.GET_ALREADY_WATCHED_MOVIES.value
            )
        )
    return output
