-- migrate:up

CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(60) NOT NULL,
    isbn VARCHAR(30) UNIQUE NOT NULL,
    pages INTEGER NOT NULL,
    publication_year INTEGER NOT NULL,
    edition_year INTEGER NOT NULL,
    synopsis TEXT,
    cover_image VARCHAR(100) DEFAULT NULL,
    pdf VARCHAR(100) DEFAULT NULL,
    publisher_id INTEGER,
    FOREIGN KEY (publisher_id) REFERENCES books(id)
);

-- migrate:down

DROP TABLE books;