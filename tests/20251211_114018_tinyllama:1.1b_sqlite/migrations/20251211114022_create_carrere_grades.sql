-- migrate:up

CREATE TABLE carrere_grades (
  id INTEGER PRIMARY KEY,
  name VARCHAR(40) NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS carrere_grades;