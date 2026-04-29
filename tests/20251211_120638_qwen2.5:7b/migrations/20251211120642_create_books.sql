-- migrate:up

CREATE TABLE books (
  id SERIAL PRIMARY KEY,
  title VARCHAR(60) NOT NULL UNIQUE,
  isbn VARCHAR(30),
  pages INTEGER NOT NULL CHECK (pages > 0),
  publication_year INTEGER CHECK (publication_year > 0),
  edition_year INTEGER CHECK (edition_year > 0),
  synopsis TEXT,
  cover_image VARCHAR(100),
  pdf VARCHAR(100),
  publisher_id INTEGER REFERENCES publishers(id)
);

-- migrate:down

DROP TABLE books;