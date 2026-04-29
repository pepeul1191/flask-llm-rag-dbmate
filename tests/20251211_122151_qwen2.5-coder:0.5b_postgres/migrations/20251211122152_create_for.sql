-- migrate:up

Create table for users
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(20),
  -- Add other columns as needed
);

-- migrate:down

DROP TABLE IF EXISTS for;