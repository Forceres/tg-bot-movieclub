from os import chdir, getcwd
from os.path import join

from db_interaction import db_interaction


def delete_db() -> None:
    path = getcwd()
    with open(
        join(path, "src", "db", "migrations", "db_delete.sql"), "rt"
    ) as fout:
        query = fout.read()
    chdir("src")
    db_interaction(query)
