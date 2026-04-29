-- migrate:up

CREATE TABLE books_genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id),
    (genre_id) REFERENCES genres(id)
);

-- migrate:down

DROP TABLE books_genres;