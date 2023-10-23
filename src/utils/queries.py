from enum import Enum


class Queries(Enum):
    GET_CURRENT_MOVIES = """SELECT m.director, m.title, m.year,
     m.duration, m.link, m.genres, m.countries, m.imdb_rating,
     m.suggested_by from movies_sessions
    LEFT JOIN movies m on m.id = movies_sessions.movie_id
    LEFT JOIN sessions s on s.id = movies_sessions.session_id
    WHERE s.finished_at is NULL
    """
    GET_THE_SAME_LINKS = """SELECT link FROM movies WHERE link IN (?)"""
    GET_ALREADY_WATCHED_MOVIES = """SELECT title, director, year,
     countries, genres, link, duration, imdb_rating, rating,
     finish_watch, suggested_by from movies
     WHERE finish_watch IS NOT NULL
     ORDER BY finish_watch DESC"""
    ENABLE_FOREIGN_KEYS = """PRAGMA foreign_keys = ON"""
    CREATE_VOTING = (
        """INSERT INTO votings (type) VALUES ('asc') RETURNING id"""
    )
    SYNCHRONIZE_MOVIES_VOTINGS_TABLE = (
        "INSERT INTO movies_votings (movie_id, voting_id) VALUES (?,?)"
    )
    INSERT_NEW_MOVIES = """INSERT INTO movies
    (title, description, director, year, countries, genres, link,
     duration, imdb_rating, suggested_by)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """
    UPDATE_EXISTED_MOVIES = """UPDATE movies SET
    created_at = CURRENT_TIMESTAMP, start_watch = NULL,
    finish_watch = NULL, suggested_by = '%s' WHERE link == (?)"""
