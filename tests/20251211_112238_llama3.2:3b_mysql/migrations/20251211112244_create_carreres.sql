-- migrate:up

CREATE TABLE carreres (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(40)
);

-- migrate:down

DROP TABLE IF EXISTS carreres;