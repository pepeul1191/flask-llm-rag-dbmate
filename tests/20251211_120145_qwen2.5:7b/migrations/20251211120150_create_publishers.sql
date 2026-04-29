-- migrate:up

CREATE TABLE publishers (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  logo VARCHAR(100),
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS publishers;