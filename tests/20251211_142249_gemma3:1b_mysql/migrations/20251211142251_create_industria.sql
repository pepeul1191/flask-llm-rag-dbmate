-- migrate:up

CREATE TABLE industria (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE industria;