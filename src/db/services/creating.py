from logging import getLogger
from sqlite3 import Row
from typing import Iterable

from aiosqlite import Cursor

from src.db.config.db import SqliteRepository
from src.utils.queries import Queries

logger = getLogger(__name__)


async def create_new_voting(movies_id: list) -> None:
    async with SqliteRepository() as db:
        result: Cursor = await db.single_query(Queries.CREATE_VOTING.value)
        voting_id: Row = await result.fetchone()
        await db.multi_query(
            Queries.SYNCHRONIZE_MOVIES_VOTINGS_TABLE.value,
            [[movie_id, *voting_id] for movie_id in movies_id],
        )
        await db.commit()


async def check_if_movies_exist(refs: list) -> Iterable:
    async with SqliteRepository() as db:
        query = Queries.GET_THE_SAME_LINKS.value
        cursor = await db.single_query(query, [", {}".join(refs)])
        response = await cursor.fetchall()
    if response:
        return response
    else:
        return []


async def update_existed_movies(refs: list, suggested_by):
    async with SqliteRepository() as db:
        cursor = await db.multi_query(
            Queries.UPDATE_EXISTED_MOVIES.value % suggested_by, refs
        )
        if cursor is None:
            return False
        else:
            await db.commit()
    return True


async def suggest_new_movie(movies: list) -> bool:
    async with SqliteRepository() as db:
        await db.multi_query(Queries.INSERT_NEW_MOVIES.value, movies)
        await db.commit()
    return True
