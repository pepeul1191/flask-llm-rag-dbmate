-- migrate:up

CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS genres;