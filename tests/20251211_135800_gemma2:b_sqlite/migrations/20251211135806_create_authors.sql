-- migrate:up

CREATE TABLE authors (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(60) UNIQUE,
  birth_date DATE,
  image VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS authors;