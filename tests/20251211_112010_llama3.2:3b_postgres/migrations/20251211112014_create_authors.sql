-- migrate:up

CREATE TABLE authors (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(60),
  birth_date DATE,
  image VARCHAR(100)
);

-- migrate:down

DROP TABLE authors;