-- migrate:up

CREATE TABLE permissions (
  id SERIAL PRIMARY KEY,
  name VARCHAR(40) NOT NULL,
  created DATE NOT NULL DEFAULT CURRENT_DATE,
  updated DATE NOT NULL DEFAULT CURRENT_DATE,
  role_id INTEGER NOT NULL REFERENCES roles(id)
);

-- migrate:down

DROP TABLE IF EXISTS permissions;