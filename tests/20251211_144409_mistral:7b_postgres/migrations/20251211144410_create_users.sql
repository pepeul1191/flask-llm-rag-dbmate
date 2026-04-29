-- migrate:up

CREATE TABLE users ( id SERIAL PRIMARY KEY, username VARCHAR(20), password VARCHAR(100), activation_key VARCHAR(30), reset_key VARCHAR(30), email VARCHAR(50), activated BOOLEAN, created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated TIMESTAMP WITH TIME ZONE );

-- migrate:down

DROP TABLE IF EXISTS USERS;