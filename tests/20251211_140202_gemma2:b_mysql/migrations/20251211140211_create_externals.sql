-- migrate:up

CREATE TABLE externals (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code INT NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS externals;