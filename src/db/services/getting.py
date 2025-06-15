from sqlite3 import Row
from typing import Iterable

from aiosqlite import Cursor

from src.db.config import SqliteRepository
from src.utils import Queries


async def retrieve_current_session_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(Queries.GET_CURRENT_MOVIES.value)
        output: Iterable[Row] = await cursor.fetchall()
        return output


async def retrieve_suggested_movies() -> Iterable[Row] | bool:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(Queries.GET_SUGGESTED_MOVIES.value)
        output: Iterable[Row] = await cursor.fetchall()
        return output


async def retrieve_already_watched_movies() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor: Cursor = await db.single_query(Queries.GET_ALREADY_WATCHED_MOVIES.value)
        output: Iterable[Row] = await cursor.fetchall()
        return output


async def retrieve_movies_with_max_votes() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_MAX_VOTES.value)
        movies_votings_ids = await cursor.fetchall()
        questions = ["?" for _ in movies_votings_ids]
        cursor = await db.single_query(
            Queries.GET_MOVIES_FROM_VOTES.value % ",".join(questions),
            [movie_voting_id[0] for movie_voting_id in movies_votings_ids],
        )
        output = await cursor.fetchall()
        return output


async def retrieve_movies_with_min_votes() -> Iterable[Row]:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_MIN_VOTES.value)
        movies_votings_ids = await cursor.fetchall()
        questions = ["?" for _ in movies_votings_ids]
        cursor = await db.single_query(
            Queries.GET_MOVIES_FROM_VOTES.value % ",".join(questions),
            [movie_voting_id[0] for movie_voting_id in movies_votings_ids],
        )
        output = await cursor.fetchall()
        return output


async def retrieve_voter_by_tg_id(tg_id: int) -> Row | bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_VOTER_BY_TG_ID.value, [tg_id])
        voter = await cursor.fetchone()
        if not voter:
            return False
        return voter


async def retrieve_current_voting_type() -> Row:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_CURRENT_VOTING_TYPE.value)
        voting_type = await cursor.fetchone()
        return voting_type


async def check_if_movies_exist(refs: list) -> Iterable:
    async with SqliteRepository() as db:
        query = Queries.GET_THE_SAME_LINKS.value
        questions = ",".join(["?" for _ in refs])
        cursor = await db.single_query(query % questions, refs)
        output = await cursor.fetchall()
        if output:
            return output
        else:
            return []
