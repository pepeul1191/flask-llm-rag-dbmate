**Esquema SQL Completo para MySQL**

**Objetivo**: Crear un esquema SQL completo basado en el diagrama UML proporcionado.

**Base de datos objetivo**: MySQL

**Tablas y Atributos**

```sql
-- Tabla "users"
CREATE TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(20) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  activation_key VARCHAR(30),
  reset_key VARCHAR(30),
  email VARCHAR(50) NOT NULL UNIQUE,
  activated BOOLEAN DEFAULT FALSE,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla "systems"
CREATE TABLE systems (
  id INT PRIMARY KEY,
  name VARCHAR(40) NOT NULL,
  description TEXT,
  repository VARCHAR(100),
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla "roles"
CREATE TABLE roles (
  id INT PRIMARY KEY,
  name VARCHAR(40) NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  system_id INT,
  FOREIGN KEY (system_id) REFERENCES systems(id)
);

-- Tabla "permissions"
CREATE TABLE permissions (
  id INT PRIMARY KEY,
  name VARCHAR(40) NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  role_id INT,
  FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Tabla "systems_users"
CREATE TABLE systems_users (
  system_id INT,
  user_id INT,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (system_id, user_id),
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabla "systems_users_permissions"
CREATE TABLE systems_users_permissions (
  system_id INT,
  user_id INT,
  permission_id INT,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (system_id, user_id, permission_id),
  FOREIGN KEY (system_id) REFERENCES systems(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (permission_id) REFERENCES permissions(id)
);
```

**Explicación del esquema**

El esquema SQL completo incluye las tablas y atributos originales del diagrama UML proporcionado. Las relaciones entre tablas se definen mediante llaves foráneas, y los tipos de datos utilizados se ajustan a las características de MySQL.

*   La tabla "users" almacena información sobre los usuarios, incluyendo su identificador único, nombre de usuario, contraseña, clave de activación, clave de reset, dirección de correo electrónico y estado de activación.
*   La tabla "systems" contiene información sobre los sistemas, incluyendo su identificador único, nombre y descripción.
*   La tabla "roles" almacena información sobre las roles, incluyendo su identificador único, nombre y fecha de creación y actualización.
*   La tabla "permissions" contiene información sobre las permisiones, incluyendo su identificador único, nombre y fecha de creación y actualización.
*   La tabla "systems_users" relaciona los sistemas con los usuarios, estableciéndose una relación de muchos a uno.
*   La tabla "systems_users_permissions" relaciona los sistemas y usuarios con las permisiones, estableciendo una relación de muchos a uno.

Este esquema proporciona un marco sólido para gestionar la información de los usuarios, sistemas, roles y permisiones en una base de datos MySQL.