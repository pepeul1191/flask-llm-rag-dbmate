-- migrate:up

CREATE TABLE genres (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS genres;