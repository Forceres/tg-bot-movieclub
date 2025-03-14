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
        session_id = await get_current_session()
        cursor = await db.single_query(
            Queries.CHECK_IF_MOVIE_IN_CURRENT_SESSION.value,
            [session_id, winner_id],
        )
        movie_id = await cursor.fetchone()
        if movie_id:
            await db.rollback()
            return False
        await db.single_query(
            Queries.SYNCHRONIZE_MOVIES_SESSIONS_TABLE.value,
            [winner_id[0], session_id[0]],
        )
        return True


async def get_current_session():
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor = await db.single_query(
            Queries.CHECK_IF_CURRENT_SESSION_EXISTS.value
        )
        session_id = await cursor.fetchone()
        if not session_id:
            cursor = await db.single_query(Queries.CREATE_SESSION.value)
            session_id = await cursor.fetchone()
        return session_id


async def add_movies_to_current_session(chosen_movie_ids):
    session_id = await get_current_session()
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor = await db.single_query(
            Queries.GET_MOVIES_IDS_IN_CURRENT_SESSION.value, session_id
        )
        movie_ids = await cursor.fetchall()
        movie_ids_to_add = list(
            filter(
                lambda movie_id: movie_id not in movie_ids, chosen_movie_ids
            )
        )
        if not movie_ids_to_add:
            await db.rollback()
            return False
        await db.multi_query(
            Queries.INSERT_MOVIES_INTO_CURRENT_SESSION.value,
            [(movie_id, session_id[0]) for movie_id in movie_ids_to_add],
        )
        return True


async def update_rating_and_finish_watch(data: list) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(
            Queries.UPDATE_RATING_AND_FINISH_WATCH.value, data
        )
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


async def update_existed_movies(refs: list, suggested_by: str):
    async with SqliteRepository() as db:
        await db.multi_query(
            Queries.UPDATE_EXISTED_MOVIES.value,
            [(suggested_by, *ref) for ref in refs],
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


async def finish_session() -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.FINISH_SESSION.value)
        return True
