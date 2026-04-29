-- migrate:up

CREATE TABLE carreres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS carreres;