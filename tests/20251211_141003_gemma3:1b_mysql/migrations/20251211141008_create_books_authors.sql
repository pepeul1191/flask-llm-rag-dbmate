-- migrate:up

CREATE TABLE books_authors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- migrate:down

DROP TABLE books_authors;