from sqlite3 import connect, IntegrityError, DatabaseError

from src.config import Config


def db_interaction(query: str) -> None:
    conn = connect(Config.DATABASE.value)
    cursor = conn.cursor()
    try:
        cursor.executescript(query)
    except (IntegrityError, DatabaseError):
        conn.rollback()
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()
