-- migrate:up

CREATE TABLE systems_users (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES systems(id),
    user_id INTEGER REFERENCES users(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS systems_users;