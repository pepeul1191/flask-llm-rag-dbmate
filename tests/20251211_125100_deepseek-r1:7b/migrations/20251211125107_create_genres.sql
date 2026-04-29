-- migrate:up

CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS genres;