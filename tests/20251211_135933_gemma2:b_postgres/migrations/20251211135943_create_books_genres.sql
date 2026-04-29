-- migrate:up

CREATE TABLE books_genres (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;