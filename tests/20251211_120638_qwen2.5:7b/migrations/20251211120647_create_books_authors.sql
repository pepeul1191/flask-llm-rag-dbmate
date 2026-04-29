-- migrate:up

CREATE TABLE books_authors (
  id SERIAL PRIMARY KEY,
  book_id INTEGER REFERENCES books(id),
  author_id INTEGER REFERENCES authors(id)
);

-- migrate:down

DROP TABLE books_authors;