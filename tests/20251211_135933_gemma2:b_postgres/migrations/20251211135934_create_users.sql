-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(30) NOT NULL UNIQUE,
  password VARCHAR(40) NOT NULL,
  first_names VARCHAR(50) NOT NULL,
  last_names VARCHAR(50) NOT NULL,
  email VARCHAR(30) UNIQUE,
  birth_date DATE NOT NULL,
  profile_picture VARCHAR(100) NOT NULL,
  sex BOOLEAN NOT NULL,
  reset_key VARCHAR(30) NOT NULL,
  country_id INTEGER NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS users;