-- migrate:up

CREATE TABLE carreres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40) NOT NULL,
  logo VARCHAR(100),
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  system_id INTEGER NOT NULL,
  FOREIGN KEY (system_id) REFERENCES systems (id)
);

-- migrate:down

DROP TABLE carreres;