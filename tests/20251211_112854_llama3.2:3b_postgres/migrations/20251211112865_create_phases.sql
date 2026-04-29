-- migrate:up

CREATE TABLE phases (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) NOT NULL,
  description TEXT NOT NULL,
  init_date DATE NOT NULL,
  end_date DATE NOT NULL,
  delivery_deadline DATE NOT NULL,
  evaluation_deadline DATE NOT NULL,
  revaluation_deadline DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS phases;