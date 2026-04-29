-- migrate:up

CREATE TABLE publishers (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) UNIQUE,
  logo VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS publishers;