-- migrate:up

CREATE TABLE industries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS industries;