-- migrate:up

CREATE TABLE carreres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS carreres;