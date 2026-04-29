-- migrate:up

CREATE TABLE programs (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) NOT NULL,
  description TEXT NOT NULL,
  image_url VARCHAR(60) NOT NULL,
  pdf_url VARCHAR(60) NOT NULL,
  max_participant_team INT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

DROP TABLE IF EXISTS programs;