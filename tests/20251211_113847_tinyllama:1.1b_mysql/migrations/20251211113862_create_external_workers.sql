-- migrate:up

CREATE TABLE external_workers (
  id INT AUTO_INCREMENT PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS external_workers;