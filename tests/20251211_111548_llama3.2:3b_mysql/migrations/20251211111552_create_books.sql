-- migrate:up

CREATE TABLE books (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(60),
  isbn VARCHAR(30),
  pages INT,
  publication_year INT,
  edition_year INT,
  synopsis TEXT,
  cover_image VARCHAR(100),
  pdf VARCHAR(100),
  publisher_id INT,
  FOREIGN KEY (publisher_id) REFERENCES publishers(id)
);

-- migrate:down

DROP TABLE books;