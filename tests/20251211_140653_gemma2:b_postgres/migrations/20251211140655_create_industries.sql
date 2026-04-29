-- migrate:up

CREATE TABLE industries (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS industries;