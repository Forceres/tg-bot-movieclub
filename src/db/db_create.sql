CREATE TABLE IF NOT EXISTS allowed_users
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      BIGINT                              NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS movies
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        VARCHAR                             NOT NULL UNIQUE,
    description  VARCHAR,
    year         INTEGER                             NOT NULL,
    duration     INTEGER,
    rating FLOAT,
    start_watch  TIMESTAMP,
    finish_watch TIMESTAMP,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS votings
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_id   INTEGER   NOT NULL,
    type        VARCHAR   NOT NULL,
    created_at  TIMESTAMP NOT NULL,
    finished_at TIMESTAMP NOT NULL,
    FOREIGN KEY (winner_id) REFERENCES movies (id)
);

CREATE TABLE IF NOT EXISTS current_voting
(
    id               INTEGER PRIMARY KEY,
    voting_id        INTEGER,
    first_entity_id  INTEGER,
    second_entity_id INTEGER,
    third_entity_id  INTEGER,
    FOREIGN KEY (voting_id) REFERENCES votings (id),
    FOREIGN KEY (first_entity_id) REFERENCES movies (id),
    FOREIGN KEY (second_entity_id) REFERENCES movies (id),
    FOREIGN KEY (third_entity_id) REFERENCES movies (id)
);