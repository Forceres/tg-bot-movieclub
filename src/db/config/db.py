from abc import ABC, abstractmethod
from typing import LiteralString
from logging import getLogger

from aiosqlite import (
    connect,
    Connection,
    Cursor,
    DatabaseError,
    IntegrityError,
)

from src.config import Config

logger = getLogger(__name__)


class AbstractRepository(ABC):
    """Abstract class for interaction with database. ONlY ASYNC"""

    @abstractmethod
    async def single_query(
        self, query: LiteralString, params: list | None = None
    ) -> Cursor | None:
        raise NotImplementedError

    @abstractmethod
    async def create_cursor(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close_cursor(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def query_script(self, query) -> Cursor | None:
        raise NotImplementedError

    @abstractmethod
    async def multi_query(
        self, query: LiteralString, params: list | None = None
    ) -> Cursor | None:
        raise NotImplementedError


class SqliteRepository(AbstractRepository, object):
    """Class for asynchronous interaction with database. ONLY ASYNC"""

    _conn = None
    instance: AbstractRepository

    def __new__(cls, *args, **kwargs) -> AbstractRepository:
        if not hasattr(cls, "instance"):
            cls.instance = super(SqliteRepository, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self._connection = None
        self._cursor = None

    def __await__(self) -> AbstractRepository:
        yield from self.create_connection().__await__()
        self._connection = SqliteRepository._conn
        yield from self.create_cursor().__await__()
        return self

    async def __aenter__(self) -> AbstractRepository:
        await self.create_connection()
        self._connection: Connection = SqliteRepository._conn
        await self.create_cursor()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._cursor.close()

    @classmethod
    async def create_connection(cls) -> None:
        if cls._conn is None:
            try:
                cls._conn = await connect(Config.DATABASE.value)
            except ValueError as exc:
                logger.error("Connection was not established! %s" % exc)
                cls._conn = None
            else:
                logger.info("Connection to DB was established!")

    @classmethod
    async def close(cls) -> None:
        del cls.instance
        await cls._conn.close()
        cls._conn = None

    @staticmethod
    def check_connection() -> bool:
        return bool(SqliteRepository._conn)

    async def create_cursor(self) -> None:
        if not self._cursor:
            self._cursor: Cursor = await self._connection.cursor()

    async def single_query(
        self, query: LiteralString, params: list | None = None
    ) -> Cursor | None:
        if params is None:
            params = []
        try:
            response: Cursor = await self._cursor.execute(query, params)
        except (DatabaseError, IntegrityError) as exc:
            logger.error(
                "Error while executing query -> %s, error -> %s" % (query, exc)
            )
            await self.rollback()
        else:
            logger.warning("Query completed! -> {}".format(query))
            return response

    async def query_script(self, query: LiteralString) -> Cursor | None:
        try:
            response = await self._cursor.executescript(query)
        except (DatabaseError, IntegrityError) as exc:
            logger.error(
                "Error while executing query -> %s, error -> %s" % (query, exc)
            )
            await self.rollback()
        else:
            logger.debug("Query -> %s - completed!" % query)
            return response

    async def multi_query(
        self, query: LiteralString, params: list | None = None
    ) -> Cursor | None:
        if params is None:
            params = []
        try:
            response = await self._cursor.executemany(query, params)
        except (DatabaseError, IntegrityError) as exc:
            logger.error(
                "Error while executing query -> %s, error -> %s" % (query, exc)
            )
            await self.rollback()
        else:
            logger.debug("Query -> %s - completed!" % query)
            return response

    async def commit(self) -> None:
        await self._connection.commit()

    async def rollback(self) -> None:
        await self._connection.rollback()

    async def close_cursor(self) -> None:
        await self._cursor.close()
