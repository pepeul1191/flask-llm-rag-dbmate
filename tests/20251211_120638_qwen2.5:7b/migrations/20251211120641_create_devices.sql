-- migrate:up

CREATE TABLE devices (
  id SERIAL PRIMARY KEY,
  brand VARCHAR(30) NOT NULL,
  type VARCHAR(30) NOT NULL,
  user_id INTEGER REFERENCES users(id)
);

-- migrate:down

DROP TABLE devices;