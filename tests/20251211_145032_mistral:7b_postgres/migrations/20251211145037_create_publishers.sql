-- migrate:up

CREATE TABLE publishers ( id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL, logo VARCHAR(100) );

-- migrate:down

DROP TABLE IF EXISTS PUBLISHERS;