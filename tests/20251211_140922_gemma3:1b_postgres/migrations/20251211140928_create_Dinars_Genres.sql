-- migrate:up

CREATE TABLE  Dinars_Genres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  name VARCHAR(30) NOT NULL,
  created DATETIME NOT NULL,
  updated DATETIME NOT NULL,
  repository VARCHAR(100) NOT NULL
);

-- migrate:down

DROP TABLE Dinars_Genres;