-- migrate:up

CREATE TABLE program_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS program_types;