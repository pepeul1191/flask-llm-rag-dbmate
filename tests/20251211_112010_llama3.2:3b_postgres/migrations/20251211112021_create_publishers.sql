-- migrate:up

CREATE TABLE publishers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50),
  logo VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS publishers;