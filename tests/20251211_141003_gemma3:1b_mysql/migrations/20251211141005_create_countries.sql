-- migrate:up

CREATE TABLE countries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(30) NOT NULL,
  male_demonym VARCHAR(40) NOT NULL,
  female_demonym VARCHAR(40) NOT NULL,
  flag_image VARCHAR(100)
);

-- migrate:down

DROP TABLE countries;