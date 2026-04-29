-- migrate:up

CREATE TABLE programs (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  description TEXT,
  image_url VARCHAR(60) NOT NULL,
  pdf_url VARCHAR(60),
  max_participant_team INT NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS programs;