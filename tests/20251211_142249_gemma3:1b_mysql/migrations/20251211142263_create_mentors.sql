-- migrate:up

CREATE TABLE mentors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE mentors;