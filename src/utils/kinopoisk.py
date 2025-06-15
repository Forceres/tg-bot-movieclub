from logging import getLogger
from asyncio import gather, create_task

from httpx import HTTPError, AsyncClient, Response

from src.config import Config

logger = getLogger(__name__)


def get_kinopoisk_request_data() -> tuple:
    headers = {"X-API-KEY": Config.KINOPOISK_API_KEY.value}
    url = "https://api.kinopoisk.dev/v1.4/movie/%s"
    return headers, url


async def send_single_get_request(
    client: AsyncClient,
    url: str,
    headers: dict,
    curr_endpoint: str = "",
    params: dict = None,
) -> Response:
    try:
        response = await client.get(url=url % curr_endpoint, headers=headers, params=params)
        response.raise_for_status()
    except HTTPError as exc:
        logger.error(f"HTTP error occurred within request on {url % curr_endpoint}: {exc}")
    else:
        logger.info(f"Response from Kinopoisk sucessfully retrieved -> {url % curr_endpoint}")
        return response.json()


async def get_movies_data_from_kinopoisk(ids: list) -> list[Response]:
    headers, url = get_kinopoisk_request_data()
    async with AsyncClient() as client:
        tasks = [create_task(send_single_get_request(client, url, headers, curr_id)) for curr_id in ids]
        try:
            responses = [task.json() for task in await gather(*tasks)]
            return responses
        except HTTPError as exc:
            logger.error(exc)


async def get_random_movie() -> Response:
    params = {
        "notNullFields": [
            "id",
            "name",
            "description",
            "year",
            "rating.imdb",
            "movieLength",
            "countries.name",
            "genres.name",
            "persons.enProfession",
            "persons.name",
        ],
        "isSeries": False,
    }
    headers, url = get_kinopoisk_request_data()
    async with AsyncClient(timeout=None) as client:
        response = await send_single_get_request(client, url, headers=headers, params=params, curr_endpoint="random")
        return response
