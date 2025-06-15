from enum import Enum


class Queries(Enum):
    GET_CURRENT_MOVIES = """SELECT m.director, m.title, m.year,
     m.duration, m.link, m.genres, m.countries, m.imdb_rating,
     m.suggested_by from movies_sessions
    LEFT JOIN movies m on m.id = movies_sessions.movie_id
    LEFT JOIN sessions s on s.id = movies_sessions.session_id
    WHERE s.finished_at is NULL
    """
    GET_THE_SAME_LINKS = """SELECT link FROM movies WHERE link IN (%s)"""
    GET_ALREADY_WATCHED_MOVIES = """SELECT title, director, year,
     countries, genres, link, duration, imdb_rating, rating,
     finish_watch, suggested_by from movies
     WHERE finish_watch IS NOT NULL
     ORDER BY finish_watch DESC"""
    ENABLE_FOREIGN_KEYS = """PRAGMA foreign_keys = ON"""
    CREATE_VOTING = """INSERT INTO votings (type) VALUES (?) RETURNING id"""
    SYNCHRONIZE_MOVIES_VOTINGS_TABLE = "INSERT INTO movies_votings (movie_id, voting_id) VALUES (?,?)"
    INSERT_NEW_MOVIES = """INSERT INTO movies
    (title, description, director, year, countries, genres, link,
     duration, imdb_rating, suggested_by)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """
    UPDATE_EXISTED_MOVIES = """UPDATE movies SET
    suggested_at = strftime('%Y-%m-%dT%H:%M','now', 'localtime'),
    suggested_by = (?) WHERE link = (?)"""
    GET_SUGGESTED_MOVIES = """SELECT id, title FROM movies WHERE
    strftime('%Y-%m-%d',suggested_at) > date('now','-1 month')"""
    GET_CURRENT_MOVIE_ID_AND_VOTING_ID = """
    SELECT m.id, v.id FROM movies_votings mv
    LEFT JOIN main.movies m on m.id = mv.movie_id
    LEFT JOIN main.votings v on v.id = mv.voting_id
    WHERE m.title == (?) AND v.finished_at is NULL
    """
    GET_CURRENT_VOTING_ID = """SELECT v.id FROM movies_votings mv
    LEFT JOIN main.votings v on v.id = mv.voting_id WHERE v.finished_at is NULL"""
    DEFINE_WINNER = """UPDATE votings SET winner_id = (?),
    finished_at = strftime('%Y-%m-%dT%H:%M','now', 'localtime')
    WHERE id = (?) RETURNING winner_id"""
    SYNCHRONIZE_MOVIES_SESSIONS_TABLE = """INSERT INTO movies_sessions (movie_id, session_id) VALUES (?,?)"""
    CHECK_IF_CURRENT_SESSION_EXISTS = """SELECT id FROM sessions WHERE finished_at is NULL"""
    CREATE_SESSION = """INSERT INTO sessions DEFAULT VALUES RETURNING id"""
    UPDATE_RATING_AND_FINISH_WATCH = """UPDATE movies SET rating = (?),
    finish_watch = strftime('%Y-%m-%dT%H:%M','now', 'localtime')
    WHERE title = (?)"""
    DELETE_CURRENT_VOTING = """DELETE FROM votings WHERE finished_at IS NULL"""
    FINISH_SESSION = """UPDATE sessions SET
    finished_at = strftime('%Y-%m-%dT%H:%M','now', 'localtime')"""
    GET_MOVIES_IDS_IN_CURRENT_SESSION = """SELECT movie_id FROM movies_sessions WHERE session_id = (?)"""
    CHECK_IF_MOVIE_IN_CURRENT_SESSION = """SELECT movie_id FROM movies_sessions
    WHERE session_id = (?) AND movie_id = (?)"""
    INSERT_MOVIES_INTO_CURRENT_SESSION = """INSERT INTO movies_sessions (movie_id, session_id) VALUES (?,?)"""
    GET_MOVIE_ID_BY_TITLE = """SELECT id FROM movies WHERE title = (?)"""
    GET_MOVIE_TITLE_BY_ID = """SELECT title FROM movies WHERE id = (?)"""
    CREATE_VOTER = """INSERT INTO voters (tg_id) VALUES (?)"""
    ADD_VOTE = """INSERT INTO movies_votings_voters (movie_voting_id, voter_id) VALUES (?,?)"""
    ADD_RATING_VOTE = """INSERT INTO movies_rating_voters (movie_id, voter_id, chosen_value) VALUES (?,?,?)"""
    GET_MOVIE_VOTING_ID_BY_TITLE = """SELECT id FROM movies_votings 
    WHERE movie_id IN (SELECT id FROM movies WHERE title IN (%s)) AND voting_id = (%s)"""
    DELETE_VOTES = """DELETE FROM movies_votings_voters WHERE voter_id = (?)"""
    GET_MAX_VOTES = """WITH counted_votes AS (
    SELECT movie_voting_id, COUNT(*) AS counter
    FROM movies_votings_voters
    GROUP BY movie_voting_id)
    SELECT movie_voting_id
    FROM counted_votes
    WHERE counter = (SELECT MAX(counter) FROM counted_votes);"""
    DELETE_ALL_VOTES = """DELETE FROM movies_votings_voters"""
    GET_MIN_VOTES = """WITH counted_votes AS (
    SELECT movie_voting_id, COUNT(*) AS counter
    FROM movies_votings_voters
    GROUP BY movie_voting_id)
    SELECT movie_voting_id
    FROM counted_votes
    WHERE counter = (SELECT MIN(counter) FROM counted_votes)"""
    GET_ALL_VOTES = """
    SELECT COUNT(*), movie_voting_id AS counter
    FROM movies_votings_voters
    GROUP BY movie_voting_id
    """
    ASSIGN_VOTES_AFTER_VOTING = """UPDATE movies_votings SET total_votes = (?) WHERE id = (?)"""
    CREATE_JOB = """INSERT INTO jobs 
    (name, func_to_do, module_path, planned_at, message_id, extra_data) 
    VALUES (?,?,?,?,?,?)"""
    DELETE_JOB = """DELETE FROM jobs WHERE name = (?)"""
    GET_VOTER_BY_TG_ID = """SELECT id FROM voters WHERE tg_id = (?)"""
    GET_CURRENT_VOTING_TYPE = """SELECT type FROM votings WHERE finished_at IS NULL"""
    GET_MOVIES_FROM_VOTES = """SELECT m.title FROM movies_votings mv
    LEFT JOIN main.movies m on m.id = mv.movie_id WHERE mv.id IN (%s)"""
    GET_RATING_AVERAGE = """
    SELECT AVG(chosen_value)
    FROM movies_rating_voters
    LEFT JOIN main.movies m on m.id = movie_id
    WHERE m.title = (?)
    GROUP BY movie_id
    """
    DELETE_RATING_VOTES = """DELETE FROM movies_rating_voters WHERE voter_id = (?)"""
    DELETE_ALL_RATING_VOTES = """DELETE FROM movies_rating_voters WHERE movie_id = (?)
    """
    GET_ALL_JOBS = """SELECT name, func_to_do, module_path, planned_at, message_id, extra_data FROM jobs"""
    START_WATCH_MOVIE = """UPDATE movies SET start_watch = strftime('%Y-%m-%dT%H:%M','now', 'localtime') WHERE id = (
    ?)"""
    EXCLUDE_MOVIE_FROM_SESSION = """DELETE FROM movies_sessions WHERE movie_id = (?)"""
    UPDATE_MOVIE_RATING = """UPDATE movies SET rating = (?) WHERE link = (?)"""
    GET_MOVIE_LINK_BY_ID = """SELECT link FROM movies WHERE id = (?)"""
    GET_CURRENT_SESSION_MOVIE_BY_LINK = """SELECT movie_id FROM movies_sessions
    LEFT JOIN main.movies m on m.id = movie_id
    LEFT JOIN main.sessions s on s.id = session_id
    WHERE m.link = (?) AND s.finished_at IS NULL
    """
