-- migrate:up

CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(60),
    birth_date DATE,
    image VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS authors;