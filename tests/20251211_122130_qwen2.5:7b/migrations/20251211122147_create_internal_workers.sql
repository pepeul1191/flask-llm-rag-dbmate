-- migrate:up

CREATE TABLE internal_workers (
    id SERIAL PRIMARY KEY,
    code INT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;