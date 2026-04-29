-- migrate:up

CREATE TABLE countries (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS countries;