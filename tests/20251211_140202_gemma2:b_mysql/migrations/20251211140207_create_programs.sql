-- migrate:up

CREATE TABLE programs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  description TEXT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS programs;