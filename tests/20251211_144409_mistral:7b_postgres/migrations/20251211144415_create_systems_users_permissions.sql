-- migrate:up

CREATE TABLE systems_users_permissions ( id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), system_id INTEGER REFERENCES systems(id), permission_id INTEGER REFERENCES permissions(id), created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );

-- migrate:down

DROP TABLE IF EXISTS SYSTEMS_USERS_PERMISSIONS;