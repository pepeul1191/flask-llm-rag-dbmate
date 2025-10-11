-- migrate:up

CREATE TABLE versions (
  id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(50) NOT NULL,
  model TEXT NOT NULL,
  created_at DATETIME,
  updated_at DATETIME,
  project_id INTEGER NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- migrate:down

DROP TABLE versions;