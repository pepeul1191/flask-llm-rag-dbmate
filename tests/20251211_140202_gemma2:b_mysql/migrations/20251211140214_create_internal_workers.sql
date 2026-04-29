-- migrate:up

CREATE TABLE internal_workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code INT REFERENCES internals(id)
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;