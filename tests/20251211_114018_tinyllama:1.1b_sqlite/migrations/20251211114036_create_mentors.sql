-- migrate:up

CREATE TABLE mentors (
  id INTEGER PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS mentors;