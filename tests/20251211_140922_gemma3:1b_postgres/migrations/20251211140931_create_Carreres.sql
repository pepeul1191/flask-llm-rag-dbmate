-- migrate:up

CREATE TABLE  Carreres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  category VARCHAR(50) NOT NULL
);

-- migrate:down

DROP TABLE Carreres;