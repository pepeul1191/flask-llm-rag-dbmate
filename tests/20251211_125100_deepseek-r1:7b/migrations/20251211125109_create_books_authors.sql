-- migrate:up

CREATE TABLE books_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    author_id INTEGER
);

-- migrate:down

DROP TABLE IF EXISTS books_authors;