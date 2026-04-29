-- migrate:up

CREATE TABLE books_authors (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  book_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;