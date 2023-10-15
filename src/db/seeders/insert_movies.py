from sqlite3 import connect, IntegrityError, DatabaseError
from json import load
from os import chdir, getcwd
from os.path import join

from src.config import Config


def insert() -> None:
    path = getcwd()
    with open(
        join(path, "src", "db", "seeders", "movies.json"),
        "rt",
        encoding="utf-8",
    ) as fout:
        data = load(fout)
    chdir(path)
    conn = connect(Config.DATABASE.value)
    cursor = conn.cursor()
    data = [
        [
            item.get("title"),
            item.get("description"),
            item.get("director"),
            item.get("year"),
            item.get("countries"),
            item.get("link"),
            item.get("duration"),
            float(item.get("rating")),
            item.get("start_watch"),
            item.get("finish_watch"),
        ]
        for item in data["movies"]
    ]
    try:
        cursor.executemany(
            """INSERT OR IGNORE INTO movies
            (title, description, director, year, countries, link,
            duration, imdb_rating, start_watch, finish_watch)
            VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING""",
            data,
        )
    except (IntegrityError, DatabaseError):
        conn.rollback()
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()
