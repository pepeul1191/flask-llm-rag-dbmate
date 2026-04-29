-- migrate:up

CREATE TABLE genres (
  id INTEGER PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS genres;