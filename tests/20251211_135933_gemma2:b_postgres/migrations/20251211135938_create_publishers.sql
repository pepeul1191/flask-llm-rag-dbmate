-- migrate:up

CREATE TABLE publishers (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  logo VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS publishers;