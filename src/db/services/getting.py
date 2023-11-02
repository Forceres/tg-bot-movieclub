from sqlite3 import Row
from typing import Iterable

from aiosqlite import Cursor

from src.db.config.db import SqliteRepository
from src.utils.queries import Queries


async def retrieve_current_session_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(
            Queries.GET_CURRENT_MOVIES.value
        )
        output: Iterable[Row] = await cursor.fetchall()
        return output


async def retrieve_suggested_movies() -> Iterable[Row] | bool:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(
            Queries.GET_SUGGESTED_MOVIES.value
        )
        output: Iterable[Row] = await cursor.fetchall()
        return output


async def retrieve_already_watched_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(
            Queries.GET_ALREADY_WATCHED_MOVIES.value
        )
        output: Iterable[Row] = await cursor.fetchall()
        return output
