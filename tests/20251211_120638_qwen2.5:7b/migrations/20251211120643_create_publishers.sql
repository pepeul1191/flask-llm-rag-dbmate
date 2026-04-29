-- migrate:up

CREATE TABLE publishers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  logo VARCHAR(100)
);

-- migrate:down

DROP TABLE publishers;