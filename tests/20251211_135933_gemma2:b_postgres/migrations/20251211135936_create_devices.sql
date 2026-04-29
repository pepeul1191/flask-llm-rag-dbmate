-- migrate:up

CREATE TABLE devices (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  brand VARCHAR(30) NOT NULL,
  type VARCHAR(30) NOT NULL,
  user_id INTEGER NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS devices;