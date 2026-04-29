-- migrate:up

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(30),
  password VARCHAR(40),
  first_names VARCHAR(50),
  last_names VARCHAR(50),
  email VARCHAR(30),
  birth_date DATE,
  profile_picture VARCHAR(100),
  sex BOOLEAN,
  reset_key VARCHAR(30),
  country_id INTEGER,
  FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- migrate:down

DROP TABLE users;