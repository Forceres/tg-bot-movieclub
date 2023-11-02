from sqlite3 import Row
from typing import Iterable

from aiosqlite import Cursor

from src.db.config.db import SqliteRepository
from src.utils.queries import Queries


async def create_new_voting(movies_id: list, voting_type: str) -> bool:
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor: Cursor = await db.single_query(
            Queries.CREATE_VOTING.value, [voting_type]
        )
        voting_id: Row = await cursor.fetchone()
        await db.multi_query(
            Queries.SYNCHRONIZE_MOVIES_VOTINGS_TABLE.value,
            [[movie_id, *voting_id] for movie_id in movies_id],
        )
        return True


async def assign_winner(winner_name: str) -> bool:
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor: Cursor = await db.single_query(
            Queries.GET_CURRENT_VOTING_ID_AND_MOVIE_ID.value, [winner_name]
        )
        ids = await cursor.fetchone()
        cursor = await db.single_query(
            Queries.DEFINE_WINNER.value, [ids[0], ids[1]]
        )
        winner_id = await cursor.fetchone()
        cursor = await db.single_query(
            Queries.CHECK_IF_CURRENT_SESSION_EXISTS.value
        )
        session_id = await cursor.fetchone()
        if not session_id:
            cursor = await db.single_query(Queries.CREATE_SESSION.value)
            session_id = await cursor.fetchone()
        await db.single_query(
            Queries.SYNCHRONIZE_MOVIES_SESSIONS_TABLE.value,
            [winner_id[0], session_id[0]],
        )
        return True


async def update_rating(data: list) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.UPDATE_RATING.value, data)
        return True


async def check_if_movies_exist(refs: list) -> Iterable:
    async with SqliteRepository() as db:
        query = Queries.GET_THE_SAME_LINKS.value
        cursor = await db.single_query(query, [", {}".join(refs)])
        output = await cursor.fetchall()
        if output:
            return output
        else:
            return []


async def update_existed_movies(refs: list, suggested_by):
    async with SqliteRepository() as db:
        await db.multi_query(
            Queries.UPDATE_EXISTED_MOVIES.value % suggested_by, refs
        )
        return True


async def suggest_new_movies(movies: list) -> bool:
    async with SqliteRepository() as db:
        await db.multi_query(Queries.INSERT_NEW_MOVIES.value, movies)
        return True


async def delete_voting() -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.DELETE_CURRENT_VOTING.value)
        return True
