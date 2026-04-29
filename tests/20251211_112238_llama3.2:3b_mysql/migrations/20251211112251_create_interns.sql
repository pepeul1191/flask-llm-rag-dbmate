-- migrate:up

CREATE TABLE interns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code INT
);

-- migrate:down

DROP TABLE IF EXISTS interns;