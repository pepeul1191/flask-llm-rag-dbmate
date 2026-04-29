-- migrate:up

CREATE TABLE books_genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    genre_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS books_genres;