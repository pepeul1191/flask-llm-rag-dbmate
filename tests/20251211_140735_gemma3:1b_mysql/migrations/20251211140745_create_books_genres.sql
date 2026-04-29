-- migrate:up

CREATE TABLE books_genres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books (id)
);

-- migrate:down

DROP TABLE books_genres;