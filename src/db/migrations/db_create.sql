CREATE TABLE IF NOT EXISTS movies
(
    id           INTEGER PRIMARY KEY,
    title        VARCHAR                             NOT NULL UNIQUE,
    description  VARCHAR,
    director     VARCHAR,
    year         INTEGER                             NOT NULL,
    countries    VARCHAR,
    genres       VARCHAR,
    link         VARCHAR                             NOT NULL UNIQUE,
    duration     INTEGER,
    imdb_rating  FLOAT,
    rating       FLOAT,
    start_watch  TIMESTAMP,
    finish_watch TIMESTAMP,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    suggested_by BIGINT
);

CREATE TABLE IF NOT EXISTS votings
(
    id          INTEGER PRIMARY KEY,
    winner_id   INTEGER,
    type        VARCHAR                             NOT NULL CHECK ( type == 'schulze' OR type == 'asc' OR type == 'desc'),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    FOREIGN KEY (winner_id) REFERENCES movies (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS movies_votings
(
    id        INTEGER PRIMARY KEY,
    movie_id  INTEGER,
    voting_id INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
    FOREIGN KEY (voting_id) REFERENCES votings (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions
(
    id          INTEGER PRIMARY KEY,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS movies_sessions
(
    id         INTEGER PRIMARY KEY,
    movie_id   INTEGER,
    session_id INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);