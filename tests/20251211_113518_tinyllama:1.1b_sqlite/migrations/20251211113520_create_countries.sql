-- migrate:up

CREATE TABLE countries (
  id INTEGER PRIMARY KEY,
  name VARCHAR(30) NOT NULL,
  male_demonym VARCHAR(40) DEFAULT 'Unknown',
  female_demonym VARCHAR(40) DEFAULT 'Unknown',
  flag_image VARCHAR(100)
);

-- migrate:down

DROP TABLE IF EXISTS countries;