-- migrate:up

CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title VARCHAR(60) NOT NULL,
  isbn VARCHAR(30) NOT NULL,
  pages INTEGER NOT NULL,
  publication_year INTEGER NOT NULL,
  edition_year INTEGER NOT NULL,
  synopsis TEXT,
  cover_image VARCHAR(100),
  pdf VARCHAR(100),
  publisher_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS books;