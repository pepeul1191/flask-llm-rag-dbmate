-- migrate:up

CREATE TABLE authors (
  id INTEGER PRIMARY KEY,
  full_name VARCHAR(60) NOT NULL,
  birth_date DATE NOT NULL,
  image VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS authors;