**Esquema SQL completo para MySQL basado en el diagrama UML proporcionado**

```sql
-- Crear la base de datos
CREATE DATABASE roles_permisos_sys_users;

-- Seleccionar la base de datos
USE roles_permisos_sys_users;

-- Crear la tabla "roles"
CREATE TABLE roles (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  system_id INTEGER,
  PRIMARY KEY (id)
);

-- Crear la tabla "permissions"
CREATE TABLE permissions (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  role_id INTEGER,
  PRIMARY KEY (id)
);

-- Crear la tabla "users"
CREATE TABLE users (
  id INTEGER AUTO_INCREMENT,
  username VARCHAR(20) NOT NULL,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30),
  reset_key VARCHAR(30),
  email VARCHAR(50) NOT NULL,
  activated BOOLEAN DEFAULT FALSE,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

-- Crear la tabla "systems"
CREATE TABLE systems (
  id INTEGER AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100),
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

-- Crear la tabla "users_systems"
CREATE TABLE users_systems (
  id INTEGER AUTO_INCREMENT,
  user_id INTEGER NOT NULL,
  system_id INTEGER NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (system_id) REFERENCES systems(id)
);

-- Crear la tabla "systems_users_permissions"
CREATE TABLE systems_users_permissions (
  id INTEGER AUTO_INCREMENT,
  system_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users_systems(user_id),
  FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

-- Crear las claves primarias y foráneas
ALTER TABLE roles ADD CONSTRAINT fk_roles_systems FOREIGN KEY (system_id) REFERENCES systems(id);
ALTER TABLE permissions ADD CONSTRAINT fk_permissions_roles FOREIGN KEY (role_id) REFERENCES roles(id);
ALTER TABLE users_systems ADD CONSTRAINT fk_users_systems_systems FOREIGN KEY (system_id) REFERENCES systems(id);
ALTER TABLE systems_users_permissions ADD CONSTRAINT fk_systems_users_permissions_systems FOREIGN KEY (system_id) REFERENCES systems(id);
ALTER TABLE systems_users_permissions ADD CONSTRAINT fk_systems_users_permissions_users_systems FOREIGN KEY (user_id) REFERENCES users_systems(user_id);
ALTER TABLE permissions ADD CONSTRAINT fk_permissions_user_systems FOREIGN KEY (role_id) REFERENCES roles(id);

-- No hay constraints adicionales
```

**Explicación breve del esquema**

Este esquema SQL completo se basa en el diagrama UML proporcionado y cuenta con las siguientes características:

*   Los nombres de las tablas y atributos se mantienen originales al archivo `.puml`.
*   Se definen las claves primarias y foráneas para mantener la integridad de los datos.
*   Se utilizan tipos de datos apropiados para MySQL, como `AUTO_INCREMENT` para las claves primarias, `VARCHAR(40)` para nombres de roles y permisos, y `BOOLEAN` para el campo `activated`.
*   No se incluyen indices adicionales.

El esquema consta de 6 tablas: `roles`, `permissions`, `users`, `systems`, `users_systems` y `systems_users_permissions`. Estas tablas están relacionadas entre sí mediante claves foráneas, lo que permite mantener la integridad de los datos.