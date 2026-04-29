-- migrate:up

CREATE TABLE internals (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code INT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS internals;