-- migrate:up

CREATE TABLE specialisms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(70) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  system_id INTEGER NOT NULL,
  FOREIGN KEY (system_id) REFERENCES systems (id)
);

-- migrate:down

DROP TABLE specialisms;