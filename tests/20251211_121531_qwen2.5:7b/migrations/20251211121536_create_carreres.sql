-- migrate:up

CREATE TABLE carreres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(40),
    industry_id INTEGER,
    FOREIGN KEY (industry_id) REFERENCES industries(id)
);

-- migrate:down

DROP TABLE IF EXISTS carreres;