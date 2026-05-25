## Context

El proyecto tiene dos servicios containerizados (`django-api` y `auth-service`) con sus Dockerfiles listos, pero sin orquestación. Para el desarrollo local, un desarrollador necesita iniciar PostgreSQL, configurar variables de entorno manualmente y arrancar cada servicio por separado. Esta fase introduce docker-compose como la herramienta de orquestación para desarrollo.

Servicios que componen el stack:
- **postgres:15** — base de datos principal, compartida por `django-api` y `java-auth`
- **redis:7-alpine** — provisionado para fases futuras (Django Channels, cache)
- **zookeeper + kafka** — provisionados para fase 4 (mensajería de eventos)
- **django-api** — API REST, build local desde `./django-api`
- **java-auth** — microservicio de autenticación, build local desde `./auth-service`
- **nginx:alpine** — único punto de entrada público en el puerto 80

## Goals / Non-Goals

**Goals:**
- Stack arrancable con un solo `docker compose up -d`
- Orden de arranque correcto con healthchecks
- Credenciales fuera del repositorio
- Nginx como reverse proxy unificado

**Non-Goals:**
- TLS/HTTPS (fase posterior)
- Múltiples entornos via profiles
- Despliegue en producción/Kubernetes
- Monitoreo o logging centralizado

## Decisions

### D1 — Red bridge nombrada en lugar de la red por defecto

Se define explícitamente `app-network` como red bridge en lugar de usar la red por defecto de compose. Esto permite referenciar el nombre en documentación y futuros cambios sin depender del nombre generado automáticamente (`<proyecto>_default`).

### D2 — Volumen nombrado para postgres en lugar de bind mount

Se usa `postgres_data` como volumen nombrado gestionado por Docker, no un bind mount a una carpeta local. Los volúmenes nombrados son portables, no tienen problemas de permisos entre OS, y `docker compose down` no los elimina por defecto (requiere `-v` explícito).

### D3 — Nginx con strip de prefijo en proxy_pass

Las URLs internas de los servicios no tienen prefijo (`/tournaments/`, no `/api/tournaments/`). Nginx stripea el prefijo antes de proxear:
- `location /api/` → `proxy_pass http://django-api:8000/` (la `/` final hace el strip)
- `location /auth/` → `proxy_pass http://java-auth:8080/` (idem)

Alternativa descartada: configurar Django y Spring Boot para responder bajo prefijo — innecesariamente invasivo en el código de la aplicación.

### D4 — depends_on con service_healthy solo para postgres

`django-api` y `java-auth` esperan a que postgres esté sano. Redis y Kafka no son dependencias de arranque aún (se integran en fases 4 y 6). Agregar dependencias innecesarias ralentiza el arranque del stack.

### D5 — Kafka healthcheck via kafka-topics list

El healthcheck más fiable para Kafka en la imagen `confluentinc/cp-kafka` es intentar listar topics en el bootstrap-server local. Alternativas como `nc -z localhost 9092` detectan que el puerto está abierto pero no que el broker está listo para aceptar producers/consumers.

### D6 — .env en la raíz del proyecto, referenciado implícitamente

Docker Compose carga automáticamente el archivo `.env` de la misma carpeta desde donde se ejecuta. No es necesario declarar `env_file:` explícito. Esto reduce configuración y es el comportamiento estándar esperado.

## Risks / Trade-offs

- **[Kafka healthcheck lento]** → Kafka puede tardar 30-60s en arrancar. Mitigación: 10 reintentos con intervalo de 15s = hasta 150s de espera. Aceptable para desarrollo local.
- **[Confluentinc images y ARM]** → Las imágenes de Confluent tienen soporte limitado en Apple Silicon. Mitigación: documentado en `.env.example`; para ARM se puede usar `confluentinc/cp-kafka:latest` con platform `linux/amd64`.
- **[django-api sin esperar java-auth]** → django-api arranca sin garantía de que java-auth esté listo. Las primeras peticiones autenticadas pueden fallar hasta que java-auth responda. Mitigación: `restart: unless-stopped` en django-api y reintentos en el middleware JWT.

## Migration Plan

No hay datos existentes que migrar. Para levantar el stack por primera vez:

1. Copiar `.env.example` a `.env` y completar los valores
2. `docker compose up -d`
3. Ejecutar migraciones de Django: `docker compose exec django-api python manage.py migrate`
4. Verificar: `curl http://localhost/auth/register`

Rollback: `docker compose down` elimina contenedores. `docker compose down -v` elimina también el volumen de datos.
