-- migrate:up

CREATE TABLE books_genres (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;