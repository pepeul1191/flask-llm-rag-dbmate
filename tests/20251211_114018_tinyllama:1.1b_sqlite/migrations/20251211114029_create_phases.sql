-- migrate:up

CREATE TABLE phases (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  description TEXT,
  init_date DATE NOT NULL,
  end_date DATE NOT NULL,
  delivery_deadline DATE NOT NULL,
  evaluation_deadline DATE NOT NULL,
  revaluation_deadline DATE NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS phases;