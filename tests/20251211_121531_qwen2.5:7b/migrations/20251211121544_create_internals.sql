-- migrate:up

CREATE TABLE internals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code INT
);

-- migrate:down

DROP TABLE IF EXISTS internals;