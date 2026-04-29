-- migrate:up

CREATE TABLE programs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30),
  description TEXT,
  image_url VARCHAR(60),
  pdf_url VARCHAR(60),
  max_participant_team INTEGER,
  created_at DATETIME,
  updated_at DATETIME,
  FOREIGN KEY (id) REFERENCES dni_types(id)
);

-- migrate:down

DROP TABLE IF EXISTS programs;