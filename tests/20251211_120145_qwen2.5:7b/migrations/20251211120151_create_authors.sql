-- migrate:up

CREATE TABLE authors (
  id INTEGER AUTO_INCREMENT,
  full_name VARCHAR(60) NOT NULL,
  birth_date DATE,
  image VARCHAR(100),
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS authors;