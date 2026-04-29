-- migrate:up

CREATE TABLE systems (
  id SERIAL PRIMARY KEY,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100) NOT NULL,
  created DATE NOT NULL DEFAULT CURRENT_DATE,
  updated DATE NOT NULL DEFAULT CURRENT_DATE
);

-- migrate:down

DROP TABLE IF EXISTS systems;