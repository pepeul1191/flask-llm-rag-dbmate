-- migrate:up

CREATE TABLE books_authors (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT,
  author_id INT,
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- migrate:down

DROP TABLE books_authors;