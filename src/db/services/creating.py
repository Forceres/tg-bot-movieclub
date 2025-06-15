from logging import getLogger
from sqlite3 import Row

from aiosqlite import Cursor

from src.db.config import SqliteRepository
from src.utils import Queries


logger = getLogger(__name__)


async def create_new_voting(movies_id: list, voting_type: str) -> bool:
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor: Cursor = await db.single_query(Queries.CREATE_VOTING.value, [voting_type])
        voting_id: Row = await cursor.fetchone()
        await db.multi_query(
            Queries.SYNCHRONIZE_MOVIES_VOTINGS_TABLE.value,
            [[movie_id, *voting_id] for movie_id in movies_id],
        )
        return True


async def assign_winner(winner_name: str) -> bool:
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor: Cursor = await db.single_query(Queries.GET_CURRENT_MOVIE_ID_AND_VOTING_ID.value, [winner_name])
        ids = await cursor.fetchone()
        cursor = await db.single_query(Queries.DEFINE_WINNER.value, [ids[0], ids[1]])
        winner_id = await cursor.fetchone()
        await db.single_query(Queries.START_WATCH_MOVIE.value, [winner_id[0]])
        cursor = await db.single_query(Queries.CHECK_IF_CURRENT_SESSION_EXISTS.value)
        session_id = await cursor.fetchone()
        if not session_id:
            cursor = await db.single_query(Queries.CREATE_SESSION.value)
            session_id = await cursor.fetchone()
        cursor = await db.single_query(
            Queries.CHECK_IF_MOVIE_IN_CURRENT_SESSION.value,
            [session_id[0], winner_id[0]],
        )
        movie_id = await cursor.fetchone()
        if movie_id:
            logger.error("Movie already assigned -> %s" % movie_id)
            return False
        await db.single_query(
            Queries.SYNCHRONIZE_MOVIES_SESSIONS_TABLE.value,
            [winner_id[0], session_id[0]],
        )
        return True


async def add_movies_to_current_session(chosen_movie_ids):
    async with SqliteRepository() as db:
        await db.single_query("BEGIN")
        cursor = await db.single_query(Queries.CHECK_IF_CURRENT_SESSION_EXISTS.value)
        session_id = await cursor.fetchone()
        if not session_id:
            cursor = await db.single_query(Queries.CREATE_SESSION.value)
            session_id = await cursor.fetchone()
        cursor = await db.single_query(Queries.GET_MOVIES_IDS_IN_CURRENT_SESSION.value, session_id)
        movie_ids = await cursor.fetchall()
        movie_ids_to_add = list(
            filter(lambda movie_id: movie_id not in [m_id[0] for m_id in movie_ids], chosen_movie_ids)
        )
        if not movie_ids_to_add:
            logger.error("Movies already assigned -> %s" % chosen_movie_ids)
            return False
        await db.multi_query(
            Queries.INSERT_MOVIES_INTO_CURRENT_SESSION.value,
            [(movie_id, session_id[0]) for movie_id in movie_ids_to_add],
        )
        return True


async def update_rating_and_finish_watch(data: list) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.UPDATE_RATING_AND_FINISH_WATCH.value, data)
        return True


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


async def create_voter(tg_id: int) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_VOTER_BY_TG_ID.value, [tg_id])
        voter = await cursor.fetchone()
        if voter:
            return False
        await db.single_query(Queries.CREATE_VOTER.value, [tg_id])
        return True


async def add_votes(titles: list, tg_id: int) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_CURRENT_VOTING_ID.value)
        voting_id = await cursor.fetchone()
        questions = ["?" for _ in titles]
        cursor = await db.single_query(
            Queries.GET_MOVIE_VOTING_ID_BY_TITLE.value % (",".join(questions), voting_id[0]),
            titles,
        )
        movie_voting_ids = await cursor.fetchall()
        cursor = await db.single_query(Queries.GET_VOTER_BY_TG_ID.value, [tg_id])
        voter_id = await cursor.fetchone()
        await db.multi_query(
            Queries.ADD_VOTE.value,
            [(movie_voting_id[0], voter_id[0]) for movie_voting_id in movie_voting_ids],
        )
        return True


async def add_rating_vote(title: str, tg_id: int, chosen_value) -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_MOVIE_ID_BY_TITLE.value, [title])
        movie_id = await cursor.fetchone()
        cursor = await db.single_query(Queries.GET_VOTER_BY_TG_ID.value, [tg_id])
        voter_id = await cursor.fetchone()
        await db.single_query(
            Queries.ADD_RATING_VOTE.value,
            [movie_id[0], voter_id[0], chosen_value],
        )
        return True


async def assign_votes_after_voting() -> bool:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_ALL_VOTES.value)
        votes = await cursor.fetchall()
        if not votes:
            return False
        await db.multi_query(Queries.ASSIGN_VOTES_AFTER_VOTING.value, [*votes])
        return True


async def create_jobs(job_data: list) -> bool:
    async with SqliteRepository() as db:
        if isinstance(job_data[0], list):
            await db.multi_query(Queries.CREATE_JOB.value, job_data)
        else:
            await db.single_query(Queries.CREATE_JOB.value, job_data)
        return True


async def calculate_rating(title: str) -> Row:
    async with SqliteRepository() as db:
        cursor = await db.single_query(Queries.GET_RATING_AVERAGE.value, [title])
        rating = await cursor.fetchone()
        return rating


async def update_movie_rating(link: str, rating: float) -> bool:
    async with SqliteRepository() as db:
        await db.single_query(Queries.UPDATE_MOVIE_RATING.value, [link, rating])
        return True
