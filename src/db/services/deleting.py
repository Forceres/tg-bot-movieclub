from logging import getLogger

from src.db.config import SqliteRepository
from src.utils import Queries

logger = getLogger(__name__)


async def finish_session() -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.FINISH_SESSION.value)
        return True


async def delete_all_votes() -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.DELETE_ALL_VOTES.value)
        return True


async def delete_certain_votes(user_id: int) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.DELETE_VOTES.value, [user_id])
        return True


async def delete_all_rating_votes_of_movie(title: str) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_MOVIE_ID_BY_TITLE.value, [title])
        movie_id = await cursor.fetchone()
        await db.single_query(Queries.DELETE_ALL_RATING_VOTES.value, [movie_id[0]])
        return True


async def delete_certain_rating_votes(tg_id: int) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_VOTER_BY_TG_ID.value, [tg_id])
        voter_id = await cursor.fetchone()
        await db.single_query(Queries.DELETE_VOTES.value, [voter_id[0]])
        return True


async def delete_voting() -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.DELETE_CURRENT_VOTING.value)
        return True


async def delete_jobs(name) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.DELETE_JOB.value, [name])
        return True


async def delete_movie_from_session(link: str) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_CURRENT_SESSION_MOVIE_BY_LINK.value, [link])
        movie_id = await cursor.fetchone()
        if not movie_id:
            logger.error("Could not find movie with the link -> %s" % link)
            return False
        await db.single_query(Queries.EXCLUDE_MOVIE_FROM_SESSION.value, [movie_id])
        return True
