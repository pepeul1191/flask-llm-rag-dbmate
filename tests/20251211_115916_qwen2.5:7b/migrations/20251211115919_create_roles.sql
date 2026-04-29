-- migrate:up

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP,
    system_id INTEGER REFERENCES systems(id)
);

-- migrate:down

DROP TABLE IF EXISTS roles;