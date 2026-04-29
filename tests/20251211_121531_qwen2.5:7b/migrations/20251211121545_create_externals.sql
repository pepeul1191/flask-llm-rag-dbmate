-- migrate:up

CREATE TABLE externals (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

-- migrate:down

DROP TABLE IF EXISTS externals;