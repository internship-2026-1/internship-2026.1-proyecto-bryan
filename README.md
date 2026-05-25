# Internship 2026.1 Proyecto Bryan

Sistema híbrido de inventario y ventas con integración Odoo.

## Descripción del Proyecto

Este proyecto implementa una arquitectura de microservicios para gestionar inventario, ventas y usuarios con integración al ERP Odoo. El sistema permite sincronizar productos desde Odoo, gestionar órdenes de venta y autenticar usuarios mediante JWT.

### Características Principales

- **Autenticación JWT**: Sistema de login con tokens JWT para acceso seguro
- **Sincronización con Odoo**: Integración vía XML-RPC para importar productos del ERP
- **Gestión de Inventario**: Catálogo de productos almacenado en MongoDB
- **Órdenes de Venta**: Sistema de órdenes en PostgreSQL
- **Procesamiento Asíncrono**: Cola de tareas con Celery + Redis
- **API Gateway**: Nginx como punto de entrada único y balanceador

## Servicios

### Gateway (Nginx)
- **Puerto**: 8080
- **Función**: API Gateway y reverse proxy
- **Rutas**:
  - `/user/*` → svc-users (autenticación y usuarios)
  - `/core/*` → svc-core (inventario y órdenes)
  - `/product/*` → svc-core (sincronización de productos)

### svc-users (Django)
- **Puerto**: 8000
- **Base de datos**: PostgreSQL (db-users-pg)
- **Funcionalidades**:
  - Registro y autenticación de usuarios
  - Generación de tokens JWT
  - Gestión de perfiles de usuario
- **Endpoints principales**:
  - `POST /user/api/v1/auth/login` - Login de usuario
  - `POST /user/api/v1/auth/register` - Registro de usuario

### svc-core (Django)
- **Puerto**: 8000 (interno)
- **Base de datos**:
  - PostgreSQL (db-core-pg) - Órdenes de venta
  - MongoDB (db-core-mongo) - Catálogo de productos
- **Funcionalidades**:
  - Sincronización de productos desde Odoo
  - Gestión de inventario
  - Procesamiento de órdenes de venta
- **Endpoints principales**:
  - `POST /core/api/v1/integrate/products/` - Sincronizar productos desde Odoo
  - `GET /core/api/v1/products/` - Listar productos

### svc-core-worker (Celery)
- **Función**: Procesamiento de tareas asíncronas
- **Broker**: Redis
- **Tareas**:
  - Sincronización masiva de productos
  - Procesamiento de órdenes en background

### Bases de Datos
- **db-users-pg**: PostgreSQL 15 - Usuarios y autenticación
- **db-core-pg**: PostgreSQL 15 - Órdenes de venta
- **db-core-mongo**: MongoDB 7.0 - Catálogo de productos
- **Redis**: 7-alpine - Cola de mensajes para Celery

### Herramientas de Administración
- **admin-pgadmin**: PgAdmin 4 (puerto 5050) - Administración PostgreSQL
- **admin-mongo**: Mongo Express (puerto 8081) - Administración MongoDB

## Stack Tecnológico

- **Orquestación**: Docker Compose (10 servicios)
- **Backend**: Django 4.2 + Django REST Framework 3.15
- **Base de datos NoSQL**: MongoDB 7.0 (inventario)
- **Base de datos SQL**: PostgreSQL 15 (usuarios, órdenes)
- **Cola de tareas**: Celery 5.3 + Redis 7
- **ERP**: Odoo SaaS (internship2026.odoo.com)
- **Integración**: XML-RPC
- **Gateway**: Nginx 1.25-alpine
- **Admin**: PgAdmin 4, Mongo Express

## Instalación

### Prerrequisitos
- Docker y Docker Compose (o Podman)
- Python 3.11+ (para desarrollo local)

### Configuración de Variables de Entorno

Copiar y configurar el archivo `.env`:

```bash
cp .env.example .env
```

Variables principales:
- `USERS_POSTGRES_DB`, `USERS_POSTGRES_USER`, `USERS_POSTGRES_PASSWORD`
- `CORE_POSTGRES_DB`, `CORE_POSTGRES_USER`, `CORE_POSTGRES_PASSWORD`
- `CORE_MONGO_DB_NAME`
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
- `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`
- `ADMIN_MONGO_USER`, `ADMIN_MONGO_PASS`

### Iniciar Servicios

```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar estado de los servicios
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs -f svc-users
docker-compose logs -f svc-core
```

### Migraciones de Base de Datos

```bash
# Para svc-users
docker-compose exec svc-users python manage.py migrate

# Para svc-core
docker-compose exec svc-core python manage.py migrate
```

### Crear Superusuario

```bash
# Para svc-users
docker-compose exec svc-users python manage.py createsuperuser

# Para svc-core
docker-compose exec svc-core python manage.py createsuperuser
```

## 🔧 Desarrollo

### Estructura del Proyecto

```
internship-2026.1-proyecto-bryan/
├── services/
│   ├── users/          # Servicio de usuarios
│   │   ├── apps/       # Aplicaciones Django
│   │   ├── config/     # Configuración (settings, urls)
│   │   └── Dockerfile
│   └── core/           # Servicio core (inventario, órdenes)
│       ├── inventory/  # Módulo de inventario
│       ├── orders/     # Módulo de órdenes
│       ├── config/     # Configuración
│       └── Dockerfile
├── .env                # Variables de entorno
├── docker-compose.yml  # Orquestación de servicios
└── nginx.conf          # Configuración del gateway
```

### Volumenes en Desarrollo

Los servicios `svc-users` y `svc-core` tienen volúmenes montados para desarrollo:
- Cambios en el código local se reflejan automáticamente en los containers
- No es necesario reconstruir las imágenes después de cambios

### Reconstrucción de Imágenes

```bash
# Reconstruir imagen de un servicio específico
docker-compose build svc-users
docker-compose build svc-core

# Reconstruir todas las imágenes
docker-compose build
```

## 🌐 Endpoints API

### Autenticación (svc-users)
- `POST /user/api/v1/auth/login` - Login con username/password
- `POST /user/api/v1/auth/register` - Registro de nuevo usuario
- `GET /user/api/v1/auth/me` - Obtener información del usuario actual

### Inventario (svc-core)
- `POST /core/api/v1/integrate/products/` - Sincronizar productos desde Odoo
- `GET /core/api/v1/products/` - Listar todos los productos
- `GET /core/api/v1/products/{id}/` - Obtener detalle de un producto

### Órdenes (svc-core)
- `POST /core/api/v1/orders/` - Crear nueva orden
- `GET /core/api/v1/orders/` - Listar órdenes
- `GET /core/api/v1/orders/{id}/` - Obtener detalle de orden

## 🔍 Monitoreo y Logs

### Ver Logs
```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f svc-users
docker-compose logs -f svc-core
docker-compose logs -f svc-core-worker
```

### Health Checks
Los servicios de base de datos tienen health checks configurados:
- PostgreSQL: `pg_isready`
- MongoDB: `db.adminCommand('ping')`
- Redis: `redis-cli ping`

### Herramientas de Administración
- **PgAdmin**: http://localhost:5050
- **Mongo Express**: http://localhost:8081


## 🛑 Detener Servicios

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (cuidado: se pierden datos)
docker-compose down -v
```

## 📝 Notas Importantes

- Los datos de las bases de datos persisten en volúmenes Docker
- Para desarrollo local, los volúmenes de código permiten hot-reload
- La integración con Odoo requiere credenciales válidas
- El gateway Nginx maneja el routing entre microservicios
- Las tareas de sincronización con Odoo se ejecutan en background vía Celery
