-- migrate:up

CREATE TABLE books_authors ( id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, author_id INTEGER, FOREIGN KEY (book_id) REFERENCES books(id), FOREIGN KEY (author_id) REFERENCES authors(id) );

-- migrate:down

DROP TABLE IF EXISTS BOOKS_AUTHORS;