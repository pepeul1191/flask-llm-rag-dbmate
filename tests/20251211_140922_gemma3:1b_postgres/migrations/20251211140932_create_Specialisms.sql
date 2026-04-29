-- migrate:up

CREATE TABLE  Specialisms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(70) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  repository VARCHAR(100) NOT NULL,
  created VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE Specialisms;