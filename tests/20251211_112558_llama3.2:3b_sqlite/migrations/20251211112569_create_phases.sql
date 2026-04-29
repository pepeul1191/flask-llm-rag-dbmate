-- migrate:up

CREATE TABLE phases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30),
  description TEXT,
  init_date DATE,
  end_date DATE,
  delivery_deadline DATE,
  evaluation_deadline DATE,
  revaluation_deadline DATE,
  created_at DATETIME,
  updated_at DATETIME,
  FOREIGN KEY (id) REFERENCES dni_types(id)
);

-- migrate:down

DROP TABLE IF EXISTS phases;