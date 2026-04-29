-- migrate:up

CREATE TABLE systems_users_permissions (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES systems(id),
    user_id INTEGER REFERENCES users(id),
    permission_id INTEGER REFERENCES permissions(id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS systems_users_permissions;