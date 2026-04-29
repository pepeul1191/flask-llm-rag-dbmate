-- migrate:up

CREATE TABLE books_authors (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT NOT NULL,
  author_id INT NOT NULL,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;