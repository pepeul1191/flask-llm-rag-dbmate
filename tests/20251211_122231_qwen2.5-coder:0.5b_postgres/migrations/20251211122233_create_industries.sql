-- migrate:up

CREATE TABLE industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS industries;