-- migrate:up

CREATE TABLE books (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(60) NOT NULL,
  isbn VARCHAR(30) NOT NULL,
  pages INTEGER NOT NULL,
  publication_year INTEGER NOT NULL,
  edition_year INTEGER NOT NULL,
  synopsis TEXT NOT NULL,
  cover_image VARCHAR(100) NOT NULL,
  pdf VARCHAR(100) NOT NULL,
  publisher_id INT NOT NULL,
  FOREIGN KEY (publisher_id) REFERENCES publishers(id)
);

-- migrate:down

DROP TABLE IF EXISTS books;