-- migrate:up

CREATE TABLE books_genres (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT FOREIGN KEY REFERENCES books(id),
  genre_id INT FOREIGN KEY REFERENCES genres(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;