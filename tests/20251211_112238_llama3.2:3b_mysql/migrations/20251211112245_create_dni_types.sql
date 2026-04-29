-- migrate:up

CREATE TABLE dni_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS dni_types;