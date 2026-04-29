-- migrate:up

CREATE TABLE books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(60),
  isbn VARCHAR(30),
  pages INT,
  publication_year INT,
  edition_year INT,
  synopsis TEXT,
  cover_image VARCHAR(100),
  pdf VARCHAR(100),
  publisher_id INT,
  FOREIGN KEY (publisher_id) REFERENCES program_types(id)
);

-- migrate:down

DROP TABLE IF EXISTS books;