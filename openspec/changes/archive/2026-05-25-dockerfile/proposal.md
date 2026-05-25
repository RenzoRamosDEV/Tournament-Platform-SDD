## Why

Los servicios `django-api` y `auth-service` solo pueden ejecutarse con dependencias instaladas localmente. Contenerizar ambos elimina la fricción del entorno y es prerequisito obligatorio para la fase 3 del roadmap (docker-compose + Nginx).

## What Changes

- Se añade `django-api/Dockerfile` — imagen Python 3.13/Gunicorn con usuario no-root y workers configurables
- Se añade `django-api/.dockerignore` — excluye `.venv/`, caches, mutants y archivos de entorno
- Se añade `auth-service/Dockerfile` — build multi-stage Maven → JRE-Alpine con usuario no-root
- Se añade `auth-service/.dockerignore` — excluye `target/`, fuentes de test y archivos de entorno

## Capabilities

### New Capabilities

- `django-api-dockerfile`: Imagen Docker reproducible para el servicio Django/Gunicorn con configuración de workers via env var y proceso no-root
- `auth-service-dockerfile`: Imagen Docker multi-stage para el servicio Spring Boot; compila con Maven y produce runtime JRE-Alpine mínimo

### Modified Capabilities

## Impact

- **`django-api/`**: se añaden 2 archivos nuevos (`Dockerfile`, `.dockerignore`), sin modificar código existente
- **`auth-service/`**: se añaden 2 archivos nuevos (`Dockerfile`, `.dockerignore`), sin modificar código existente
- **Dependencias de imagen**: `python:3.13-slim`, `maven:3.9-eclipse-temurin-17`, `eclipse-temurin:17-jre-alpine`
- **Variable de entorno nueva**: `GUNICORN_WORKERS` (opcional, default `2`) en el contenedor Django
