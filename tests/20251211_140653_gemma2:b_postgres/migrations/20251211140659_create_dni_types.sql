-- migrate:up

CREATE TABLE dni_types (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS dni_types;