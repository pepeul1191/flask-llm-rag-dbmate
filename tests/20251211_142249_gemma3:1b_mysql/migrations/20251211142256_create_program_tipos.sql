-- migrate:up

CREATE TABLE program_tipos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30)
);

-- migrate:down

DROP TABLE program_tipos;