-- migrate:up

CREATE TABLE books (
  id INTEGER AUTO_INCREMENT,
  title VARCHAR(60) NOT NULL,
  isbn VARCHAR(30),
  pages INTEGER,
  publication_year INTEGER,
  edition_year INTEGER,
  synopsis TEXT,
  cover_image VARCHAR(100),
  pdf VARCHAR(100),
  publisher_id INTEGER,
  PRIMARY KEY (id)
);

-- migrate:down

DROP TABLE IF EXISTS books;