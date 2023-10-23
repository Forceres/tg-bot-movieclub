from logging import getLogger
from asyncio import gather, create_task

from httpx import HTTPError, AsyncClient, Response

from src.config import Config

logger = getLogger(__name__)


async def api_call(ids: list) -> list[Response]:
    headers = {"X-API-KEY": Config.KINOPOISK_API_KEY.value}
    url = "https://api.kinopoisk.dev/v1.3/movie/%s"
    async with AsyncClient() as client:
        tasks = [
            create_task(client.get(url=url % curr_id, headers=headers))
            for curr_id in ids
        ]
        try:
            responses = [task.json() for task in await gather(*tasks)]
            return responses
        except HTTPError as exc:
            logger.error(exc)
