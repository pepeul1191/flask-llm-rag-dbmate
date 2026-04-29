-- migrate:up

CREATE TABLE countries (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL,
  male_demonym VARCHAR(40),
  female_demonym VARCHAR(40),
  flag_image VARCHAR(100),
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS countries;