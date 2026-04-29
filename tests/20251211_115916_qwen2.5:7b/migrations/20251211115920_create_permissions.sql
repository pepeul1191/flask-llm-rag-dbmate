-- migrate:up

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP,
    role_id INTEGER REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;