-- migrate:up

CREATE TABLE books_genres ( id INTEGER PRIMARY KEY AUTO_INCREMENT, book_id INTEGER, genre_id INTEGER, FOREIGN KEY (book_id) REFERENCES books(id), FOREIGN KEY (genre_id) REFERENCES genres(id) );

-- migrate:down

DROP TABLE IF EXISTS BOOKS_GENRES;