CREATE TABLE IF NOT EXISTS allowed_users
(
    id         INTEGER PRIMARY KEY,
    tg_id      BIGINT                              NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS movies
(
    id           INTEGER PRIMARY KEY,
    title        VARCHAR                             NOT NULL UNIQUE,
    description  VARCHAR,
    link         VARCHAR                             NOT NULL UNIQUE,
    year         INTEGER                             NOT NULL,
    duration     INTEGER,
    imdb_rating       FLOAT,
    rating FLOAT,
    start_watch  TIMESTAMP,
    finish_watch TIMESTAMP,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS votings
(
    id          INTEGER PRIMARY KEY,
    winner_id   INTEGER   NOT NULL,
    type        VARCHAR   NOT NULL CHECK ( type == 'schulze' OR type == 'asc' OR type == 'desc'),
    created_at  TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    FOREIGN KEY (winner_id) REFERENCES movies (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions(
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    movie_id INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS current_voting
(
    id               INTEGER PRIMARY KEY,
    voting_id        INTEGER,
    first_entity_id  INTEGER,
    second_entity_id INTEGER,
    third_entity_id  INTEGER,
    FOREIGN KEY (voting_id) REFERENCES votings (id) ON DELETE CASCADE,
    FOREIGN KEY (first_entity_id) REFERENCES movies (id) ON DELETE CASCADE,
    FOREIGN KEY (second_entity_id) REFERENCES movies (id) ON DELETE CASCADE,
    FOREIGN KEY (third_entity_id) REFERENCES movies (id) ON DELETE CASCADE
);