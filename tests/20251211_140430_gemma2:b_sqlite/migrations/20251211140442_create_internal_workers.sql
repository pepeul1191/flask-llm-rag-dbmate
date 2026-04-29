-- migrate:up

CREATE TABLE internal_workers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  code INT NOT NULL,
  FOREIGN key (code) references internals(code)
);

-- migrate:down

DROP TABLE IF EXISTS internal_workers;