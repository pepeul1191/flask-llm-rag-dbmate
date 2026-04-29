-- migrate:up

CREATE TABLE mentors (
  id SERIAL PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS mentors;