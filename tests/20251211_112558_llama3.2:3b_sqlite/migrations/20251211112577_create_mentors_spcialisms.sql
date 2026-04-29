-- migrate:up

CREATE TABLE mentors_spcialisms (
  id INTEGER PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS mentors_spcialisms;