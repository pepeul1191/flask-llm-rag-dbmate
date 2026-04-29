-- migrate:up

CREATE TABLE books_genres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT,
  genre_id INT,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE books_genres;