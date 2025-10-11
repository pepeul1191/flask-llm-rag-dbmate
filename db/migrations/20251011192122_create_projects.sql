-- migrate:up

CREATE TABLE projects (
  id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  title VARCHAR(30) NOT NULL,
  description VARCHAR(180) NOT NULL,
  connection_string VARCHAR(100) NOT NULL,
  engine_id INTEGER NOT NULL,
  FOREIGN KEY (engine_id) REFERENCES engines (id)
);

-- migrate:down

DROP TABLE projects;