-- migrate:up

CREATE TABLE devices (
  id INTEGER PRIMARY KEY,
  brand VARCHAR(30)
);

-- migrate:down

DROP TABLE IF EXISTS devices;