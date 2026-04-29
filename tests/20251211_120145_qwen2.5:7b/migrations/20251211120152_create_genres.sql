-- migrate:up

CREATE TABLE genres (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS genres;