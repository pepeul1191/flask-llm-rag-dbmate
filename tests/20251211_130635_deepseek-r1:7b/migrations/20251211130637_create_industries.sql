-- migrate:up

CREATE TABLE industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS industries;