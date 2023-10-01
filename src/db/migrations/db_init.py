from os import chdir, getcwd
from os.path import join

from db_interaction import db_interaction


def init_db() -> None:
    path = getcwd()
    with open(
        join(path, "src", "db", "migrations", "db_create.sql"), "rt"
    ) as fout:
        query = fout.read()
    chdir("src")
    db_interaction(query)
