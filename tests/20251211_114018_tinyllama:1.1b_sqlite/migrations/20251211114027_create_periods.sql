-- migrate:up

CREATE TABLE periods (
  id INTEGER PRIMARY KEY,
  name VARCHAR(10),
  init_date DATE NOT NULL,
  end_date DATE NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS periods;