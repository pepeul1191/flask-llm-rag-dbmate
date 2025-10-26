-- migrate:up

-- Migración 1: Crear tabla versions para proyecto 1
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    1,
    'create_versions_table',
    1729843200,
    'CREATE TABLE versions (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL,
        model TEXT NOT NULL,
        created_at DATETIME,
        updated_at DATETIME,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    );',
    'DROP TABLE versions;',
    TRUE,
    1
);

-- Migración 2: Crear tabla users para proyecto 1
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    2,
    'create_users_table',
    1729929600,
    'CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );',
    'DROP TABLE users;',
    TRUE,
    1
);

-- Migración 3: Crear tabla posts para proyecto 2
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    3,
    'create_posts_table',
    1730016000,
    'CREATE TABLE posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );',
    'DROP TABLE posts;',
    TRUE,
    2
);

-- Migración 4: Agregar índice a posts para proyecto 2
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    4,
    'add_index_to_posts',
    1730102400,
    'CREATE INDEX idx_posts_user_id ON posts(user_id);
     CREATE INDEX idx_posts_created_at ON posts(created_at);',
    'DROP INDEX idx_posts_user_id;
     DROP INDEX idx_posts_created_at;',
    TRUE,
    2
);

-- Migración 5: Crear tabla products para proyecto 3
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    5,
    'create_products_table',
    1730188800,
    'CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );',
    'DROP TABLE products;',
    TRUE,
    3
);

-- Migración 6: Crear tabla categories para proyecto 3
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    6,
    'create_categories_table',
    1730275200,
    'CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );',
    'DROP TABLE categories;',
    TRUE,
    3
);

-- Migración 7: Tabla de relación products-categories para proyecto 3
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    7,
    'create_product_categories_table',
    1730361600,
    'CREATE TABLE product_categories (
        product_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (product_id, category_id),
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );',
    'DROP TABLE product_categories;',
    TRUE,
    3
);

-- Migración 8: Agregar columna status a products para proyecto 3
INSERT INTO migrations (id, name, timestamp, up, down, executed, project_id) VALUES (
    8,
    'add_status_to_products',
    1730448000,
    'ALTER TABLE products ADD COLUMN status VARCHAR(20) DEFAULT ''active'';',
    'ALTER TABLE products DROP COLUMN status;',
    TRUE,
    3
);

-- migrate:down

DELETE FROM migrations;
