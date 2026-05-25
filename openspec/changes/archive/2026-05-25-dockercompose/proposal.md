## Why

Actualmente cada servicio debe iniciarse manualmente con sus dependencias configuradas a mano. Sin orquestación, es imposible levantar el stack completo de forma reproducible, lo que bloquea el desarrollo local y es prerequisito de la fase 3 del roadmap.

## What Changes

- Se añade `docker-compose.yml` en la raíz — define los 7 servicios, la red `app-network` y el volumen `postgres_data`
- Se añade `nginx/nginx.conf` — reverse proxy que enruta `/api/*` a `django-api` y `/auth/*` a `java-auth`
- Se añade `.env.example` en la raíz — plantilla con todas las variables requeridas (sin secretos reales)
- Se añade `.env` a `.gitignore`

## Capabilities

### New Capabilities

- `docker-compose-stack`: Orquestación completa del stack con red interna, volumen persistente, healthchecks y orden de arranque controlado
- `nginx-reverse-proxy`: Nginx como único punto de entrada público que enruta `/api/*` y `/auth/*` a los servicios internos

### Modified Capabilities

## Impact

- **Raíz del proyecto**: se añaden `docker-compose.yml`, `.env.example`, `nginx/nginx.conf`
- **`.gitignore`**: se añade entrada para `.env`
- **Servicios afectados**: postgres, redis, zookeeper, kafka, django-api, java-auth, nginx
- **Puerto público expuesto**: solo `80` via nginx; el resto de servicios son internos a `app-network`
- **Dependencias de imagen**: `postgres:15`, `redis:7-alpine`, `confluentinc/cp-zookeeper`, `confluentinc/cp-kafka`, `nginx:alpine` + builds locales de `django-api` y `auth-service`
