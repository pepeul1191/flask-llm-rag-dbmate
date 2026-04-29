-- migrate:up

CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(60) NOT NULL,
    birth_date DATE NOT NULL,
    image VARCHAR(100) DEFAULT NULL
);

-- migrate:down

DROP TABLE authors;