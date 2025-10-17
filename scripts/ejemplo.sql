-- Generated SQL schema from UML file
-- SQLite3 compatible

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    activation_key TEXT,
    reset_key TEXT,
    email TEXT,
    activated INTEGER,
    created TEXT,
    updated TEXT
);

CREATE TABLE systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    repository TEXT,
    created TEXT,
    updated TEXT
);

CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created TEXT,
    updated TEXT,
    system_id INTEGER PRIMARY KEY AUTOINCREMENT,
    PRIMARY KEY (id, system_id)
);

CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created TEXT,
    updated TEXT,
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    PRIMARY KEY (id, role_id)
);

CREATE TABLE systems_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT,
    PRIMARY KEY (id, system_id, user_id)
);

CREATE TABLE systems_users_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT,
    PRIMARY KEY (id, system_id, user_id, permission_id)
);

CREATE INDEX idx_users_username ON users(username);

CREATE INDEX idx_users_email ON users(email);

CREATE INDEX idx_users_created ON users(created);

CREATE INDEX idx_users_updated ON users(updated);

CREATE INDEX idx_systems_name ON systems(name);

CREATE INDEX idx_systems_created ON systems(created);

CREATE INDEX idx_systems_updated ON systems(updated);

CREATE INDEX idx_roles_name ON roles(name);

CREATE INDEX idx_roles_created ON roles(created);

CREATE INDEX idx_roles_updated ON roles(updated);

CREATE INDEX idx_permissions_name ON permissions(name);

CREATE INDEX idx_permissions_created ON permissions(created);

CREATE INDEX idx_permissions_updated ON permissions(updated);

CREATE INDEX idx_systems_users_created ON systems_users(created);

CREATE INDEX idx_systems_users_permissions_created ON systems_users_permissions(created);