-- migrate:up

CREATE TABLE books_genres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT NOT NULL,
  genre_id INT NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;