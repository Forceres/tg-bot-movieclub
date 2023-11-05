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
    CREATE_VOTING = """INSERT INTO votings (type) VALUES (?) RETURNING id"""
    SYNCHRONIZE_MOVIES_VOTINGS_TABLE = (
        "INSERT INTO movies_votings (movie_id, voting_id) VALUES (?,?)"
    )
    INSERT_NEW_MOVIES = """INSERT INTO movies
    (title, description, director, year, countries, genres, link,
     duration, imdb_rating, suggested_by)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """
    UPDATE_EXISTED_MOVIES = """UPDATE movies SET
    suggested_at = strftime('%Y-%m-%dT%H:%M','now', 'localtime'),
    start_watch = NULL, finish_watch = NULL,
    suggested_by = (?) WHERE link == (?)"""
    GET_SUGGESTED_MOVIES = """SELECT id, title FROM movies WHERE
    strftime('%Y-%m-%d',suggested_at) > date('now','-1 month')"""
    GET_CURRENT_VOTING_ID_AND_MOVIE_ID = """
    SELECT m.id, v.id FROM movies_votings mv
    LEFT JOIN main.movies m on m.id = mv.movie_id
    LEFT JOIN main.votings v on v.id = mv.voting_id
    WHERE m.title == (?) AND v.finished_at is NULL
    """
    DEFINE_WINNER = """UPDATE votings SET winner_id = (?),
    finished_at = strftime('%Y-%m-%dT%H:%M','now', 'localtime')
    WHERE id == (?) RETURNING winner_id"""
    SYNCHRONIZE_MOVIES_SESSIONS_TABLE = (
        """INSERT INTO movies_sessions (movie_id, session_id) VALUES (?,?)"""
    )
    CHECK_IF_CURRENT_SESSION_EXISTS = (
        """SELECT id FROM sessions WHERE finished_at is NULL"""
    )
    CREATE_SESSION = """INSERT INTO sessions DEFAULT VALUES RETURNING id"""
    UPDATE_RATING = """UPDATE movies SET rating = (?) WHERE title == (?)"""
    DELETE_CURRENT_VOTING = """DELETE FROM votings WHERE finished_at IS NULL"""
