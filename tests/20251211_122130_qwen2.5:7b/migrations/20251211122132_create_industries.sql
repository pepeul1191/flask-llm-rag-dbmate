-- migrate:up

CREATE TABLE industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS industries;