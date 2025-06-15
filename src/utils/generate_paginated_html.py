from datetime import datetime
from math import ceil
from typing import Iterable


def generate_html(movies: Iterable) -> list:
    offset = 0
    limit = 65
    times = ceil(len([*movies]) / limit)
    pages_data = []
    for _ in range(times):
        output = "\n".join(
            [
                f"""<p><b>#{idx + 1}: {item[0]} ({item[2]})</b>
    <br><b>Режиссер: {item[1]} <br>Страны выпуска: {item[3]}</b>
    <br><b>Жанры: {item[4] if item[4] is not None else "<s>Неизвестно</s>"}</b>
    <br><b>Длительность в минутах: {item[6]}</b>
    <br><b>Рейтинг IMDb: {item[7]}</b>
    <br><b>Рейтинг КиноКласса:
    {item[8] if item[8] is not None else "<s>Отсутствует</s>"}</b>
    <br><i>Дата просмотра:
    {datetime.fromisoformat(item[9]).strftime("%d-%m-%Y %H:%M")}</i>
    <br><i>Предложен:
    {item[10] if item[10] is not None else "<s>Неизвестно</s>"}</i>
    <br><a href={item[5]}><i>Ссылка</i></a>
    </p>"""
                for idx, item in enumerate(movies[offset : offset + limit])
            ]
        )
        pages_data.append(output)
        offset += 65
    return pages_data
