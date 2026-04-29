-- migrate:up

CREATE TABLE books_authors (
  id INTEGER AUTO_INCREMENT,
  book_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;