-- migrate:up

Create table for systems
CREATE TABLE systems (
  id SERIAL PRIMARY KEY,
  name VARCHAR(40),
  description TEXT,
  -- Add other columns as needed
);

-- migrate:down

DROP TABLE IF EXISTS for;