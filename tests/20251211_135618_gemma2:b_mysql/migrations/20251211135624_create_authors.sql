-- migrate:up

CREATE TABLE authors (
  id INT PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(60) UNIQUE,
  birth_date DATE,
  image VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS authors;