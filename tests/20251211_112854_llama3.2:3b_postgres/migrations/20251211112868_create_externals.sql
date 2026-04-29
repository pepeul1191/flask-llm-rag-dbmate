-- migrate:up

CREATE TABLE externals (
  id SERIAL PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS externals;