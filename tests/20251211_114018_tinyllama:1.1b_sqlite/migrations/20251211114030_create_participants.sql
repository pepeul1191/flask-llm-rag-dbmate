-- migrate:up

CREATE TABLE participants (
  id INTEGER PRIMARY KEY,
  names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(40) NOT NULL UNIQUE,
  phone VARCHAR(40) NOT NULL UNIQUE,
  dni VARCHAR(20) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS participants;