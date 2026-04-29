-- migrate:up

CREATE TABLE books_authors (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT FOREIGN KEY REFERENCES books(id),
  author_id INT FOREIGN KEY REFERENCES authors(id)
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;