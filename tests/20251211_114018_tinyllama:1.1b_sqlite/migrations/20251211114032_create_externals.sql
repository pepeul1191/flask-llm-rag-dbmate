-- migrate:up

CREATE TABLE externals (
  id INTEGER PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS externals;