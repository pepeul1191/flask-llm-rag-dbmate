-- migrate:up

CREATE TABLE document_types (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(22) NOT NULL
);

-- migrate:down

DROP TABLE IF EXISTS document_types;