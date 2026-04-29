-- migrate:up

CREATE TABLE specialisms (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(70)
);

-- migrate:down

DROP TABLE IF EXISTS specialisms;