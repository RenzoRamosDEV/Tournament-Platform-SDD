## Context

Actualmente ambos servicios requieren entorno local configurado (Python venv o Maven instalado). La falta de imágenes Docker bloquea la fase 3 del roadmap (docker-compose, Nginx) y hace que el onboarding dependa de la máquina del desarrollador.

Estructura relevante:
- `django-api/app/` — código fuente Django; `manage.py` y paquetes viven aquí
- `django-api/requirements/requirements.txt` — dependencias Python
- `auth-service/pom.xml` + `auth-service/src/` — proyecto Maven estándar
- El artefacto Maven generado es `auth-service-0.0.1-SNAPSHOT.jar`

## Goals / Non-Goals

**Goals:**
- Imagen `django-api` construible con solo `docker build` desde `django-api/`
- Imagen `auth-service` construible con solo `docker build` desde `auth-service/` (sin Maven en el host)
- Proceso no-root en ambas imágenes
- Cache de capas optimizado (dependencias antes que código)
- Workers de Gunicorn configurables en runtime

**Non-Goals:**
- `docker-compose.yml` ni Nginx (fase 3)
- Health checks Docker (se delegan a compose/k8s)
- Push a registry
- Optimización extrema de tamaño de imagen (sin UPX, sin distroless)

## Decisions

### D1 — Imagen base Python: `python:3.13-slim`

El proyecto usa Python 3.13 (confirmado por `.venv` con `python3.13`). Se elige `slim` sobre `alpine` porque psycopg2-binary requiere libc; con Alpine se necesitaría compilar desde fuente o usar `musl`, añadiendo complejidad sin beneficio real.

Alternativa descartada: `python:3.13-alpine` — requiere `gcc`, `musl-dev`, `postgresql-dev` para psycopg2, imagen final más grande por los build tools necesarios.

### D2 — Build multi-stage para auth-service

El stage `builder` (`maven:3.9-eclipse-temurin-17`) compila el proyecto. El stage de runtime (`eclipse-temurin:17-jre-alpine`) solo recibe el `.jar`. La imagen final no contiene JDK, Maven, ni código fuente.

Alternativa descartada: copiar `.jar` pre-compilado — acopla el `docker build` al pipeline CI y hace que el Dockerfile no sea autocontenido.

### D3 — Cache de dependencias antes del código fuente

**Django**: `COPY requirements/requirements.txt` → `pip install` → `COPY app/ .`
**Java**: `COPY pom.xml` → `mvn dependency:go-offline` → `COPY src ./src` → `mvn package`

Esto garantiza que cambiar código fuente no invalida la capa de dependencias, reduciendo build times significativamente.

### D4 — Usuario no-root via usuario de sistema

Se crea `appuser` en `appgroup` como usuario de sistema (sin shell interactivo, sin home directory por defecto). El `USER appuser` se aplica justo antes del `CMD`/`ENTRYPOINT` para que los pasos de instalación anteriores (que requieren privilegios) corran como root.

### D5 — Workers Gunicorn via env var con default

`CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2}"]`

Permite ajustar sin rebuildar la imagen. Default de 2 workers es conservador y adecuado para desarrollo/staging.

## Risks / Trade-offs

- **`mvn dependency:go-offline` no es 100% exhaustivo** → algunos plugins se descargan durante `mvn package`. El cache de Maven es funcional pero no perfecto. Mitigación: aceptable, el layer de dependencias cubre la mayoría de las descargas.
- **`auth-service-*.jar` con wildcard en COPY** → si Maven genera múltiples jars (ej. con `-sources.jar`) el wildcard podría fallar. Mitigación: Spring Boot Repackage solo produce un fat-jar; los demás artefactos tienen clasificadores y nombres distintos.
- **`.dockerignore` incompleto** → archivos no ignorados pueden invalidar el cache innecesariamente. Mitigación: los `.dockerignore` definidos en specs cubren los casos principales.

## Migration Plan

No hay migración de datos. Los Dockerfiles son archivos nuevos que no modifican código existente. Para verificar:

1. `docker build -t django-api ./django-api`
2. `docker build -t auth-service ./auth-service`
3. Verificar usuario: `docker run --rm django-api whoami` → `appuser`
4. Verificar usuario: `docker run --rm auth-service whoami` → `appuser`

Rollback: eliminar los archivos añadidos (sin impacto en servicios existentes).
