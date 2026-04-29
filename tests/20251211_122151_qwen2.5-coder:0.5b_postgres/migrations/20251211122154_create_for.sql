-- migrate:up

Create table for roles
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(40),
  -- Add other columns as needed
);

-- migrate:down

DROP TABLE IF EXISTS for;