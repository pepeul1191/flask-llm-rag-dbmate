-- migrate:up

CREATE TABLE devices (
  id INTEGER PRIMARY KEY,
  brand VARCHAR(30),
  type VARCHAR(30),
  user_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS devices;