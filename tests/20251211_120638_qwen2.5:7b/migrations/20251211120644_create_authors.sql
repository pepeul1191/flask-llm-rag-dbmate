-- migrate:up

CREATE TABLE authors (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(60) NOT NULL UNIQUE,
  birth_date DATE CHECK (birth_date < CURRENT_DATE),
  image VARCHAR(100)
);

-- migrate:down

DROP TABLE authors;