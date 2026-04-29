-- migrate:up

CREATE TABLE books_genres (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  book_id INTEGER,
  genre_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;