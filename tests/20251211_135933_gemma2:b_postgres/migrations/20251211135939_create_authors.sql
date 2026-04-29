-- migrate:up

CREATE TABLE authors (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(60) NOT NULL,
  birth_date DATE NOT NULL,
  image VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS authors;