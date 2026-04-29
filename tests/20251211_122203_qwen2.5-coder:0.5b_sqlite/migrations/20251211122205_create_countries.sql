-- migrate:up

CREATE TABLE countries (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS countries;