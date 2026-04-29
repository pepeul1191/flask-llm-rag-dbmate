-- migrate:up

CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE genres;