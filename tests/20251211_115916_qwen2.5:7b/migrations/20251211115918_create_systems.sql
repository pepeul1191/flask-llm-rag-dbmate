-- migrate:up

CREATE TABLE systems (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    description TEXT,
    repository VARCHAR(100),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS systems;