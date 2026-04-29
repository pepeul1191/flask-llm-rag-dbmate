-- migrate:up

CREATE TABLE specialisms (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(70) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;