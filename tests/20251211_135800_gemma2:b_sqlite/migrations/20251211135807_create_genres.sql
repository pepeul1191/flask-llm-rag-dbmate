-- migrate:up

CREATE TABLE genres (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS genres;