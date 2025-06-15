CREATE TABLE IF NOT EXISTS movies
(
    id           INTEGER PRIMARY KEY,
    title        VARCHAR                                                            NOT NULL UNIQUE,
    description  VARCHAR,
    director     VARCHAR,
    year         INTEGER                                                            NOT NULL,
    countries    VARCHAR,
    genres       VARCHAR,
    link         VARCHAR                                                            NOT NULL UNIQUE,
    duration     INTEGER,
    imdb_rating  FLOAT,
    rating       FLOAT,
    start_watch  TIMESTAMP,
    finish_watch TIMESTAMP,
    created_at   TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL,
    suggested_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')),
    suggested_by BIGINT
);

CREATE TABLE IF NOT EXISTS votings
(
    id          INTEGER PRIMARY KEY,
    winner_id   INTEGER,
    type        VARCHAR                                                            NOT NULL CHECK (type == 'asc' OR type == 'desc'),
    created_at  TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL,
    finished_at TIMESTAMP,
    FOREIGN KEY (winner_id) REFERENCES movies (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS movies_votings
(
    id        INTEGER PRIMARY KEY,
    movie_id  INTEGER,
    voting_id INTEGER,
    total_votes INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
    FOREIGN KEY (voting_id) REFERENCES votings (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions
(
    id          INTEGER PRIMARY KEY,
    created_at  TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL,
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

CREATE TABLE IF NOT EXISTS jobs
(
    id INTEGER PRIMARY KEY,
    "name" VARCHAR(50),
    func_to_do VARCHAR(100),
    module_path VARCHAR(250),
    planned_at TIMESTAMP,
    message_id INTEGER,
    extra_data VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS movies_rating_voters (
    id INTEGER PRIMARY KEY,
    movie_id INTEGER,
    voter_id INTEGER,
    chosen_value INTEGER,
    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (voter_id) REFERENCES voters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS movies_votings_voters (
    id INTEGER PRIMARY KEY,
    movie_voting_id INTEGER,
    voter_id INTEGER,
    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL,
    FOREIGN KEY (movie_voting_id) REFERENCES movies_votings(id) ON DELETE CASCADE,
    FOREIGN KEY (voter_id) REFERENCES voters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS voters (
    id INTEGER PRIMARY KEY,
    tg_id INTEGER,
    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M', 'now', 'localtime')) NOT NULL
);