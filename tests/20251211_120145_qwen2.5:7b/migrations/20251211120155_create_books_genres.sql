-- migrate:up

CREATE TABLE books_genres (
  id INTEGER AUTO_INCREMENT,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;