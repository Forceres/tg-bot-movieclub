from sqlite3 import connect, IntegrityError, DatabaseError
from json import load
from unicodedata import normalize
from os import chdir, getcwd
from os.path import join

from src.config import Config


def insert() -> None:
    path = getcwd()
    with open(join(path, "src", "db", "seeders", "movies.json"), "rt") as fout:
        data = load(fout)
    chdir("src")
    conn = connect(Config.DATABASE.value)
    cursor = conn.cursor()
    data = [
        [
            item.get("title").encode("utf-8"),
            normalize("NFKC", item.get("description")).encode("utf-8"),
            item.get("year"),
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
        (title, description, year, link,
        duration, imdb_rating, start_watch, finish_watch)
        VALUES (?,?,?,?,?,?,?,?)""",
            data,
        )
    except (IntegrityError, DatabaseError):
        conn.rollback()
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()
