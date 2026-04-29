-- migrate:up

CREATE TABLE books (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(60) NOT NULL,
  isbn VARCHAR(30) UNIQUE,
  pages INT,
  publication_year INT,
  edition_year INT,
  synopsis TEXT,
  cover_image VARCHAR(100) NOT NULL,
  pdf VARCHAR(100) NOT NULL,
  publisher_id INT FOREIGN KEY REFERENCES publishers(id)
);

-- migrate:down

DROP TABLE IF EXISTS books;