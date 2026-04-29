-- migrate:up

CREATE TABLE devices (
  id INTEGER AUTO_INCREMENT,
  brand VARCHAR(30),
  type VARCHAR(30),
  user_id INTEGER,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS devices;