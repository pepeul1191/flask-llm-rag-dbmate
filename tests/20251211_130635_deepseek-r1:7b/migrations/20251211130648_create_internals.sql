-- migrate:up

CREATE TABLE internals (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

-- migrate:down

DROP TABLE IF EXISTS internals;