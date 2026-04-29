-- migrate:up

CREATE TABLE genres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30) NOT NULL,
  description TEXT,
  init_date DATE NOT NULL,
  end_date DATE NOT NULL,
  delivery_deadline DATE NOT NULL,
  evaluation_deadline DATE NOT NULL,
  revaluation_deadline DATE NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  program_id INTEGER,
  FOREIGN KEY (program_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE genres;