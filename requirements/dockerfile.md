# Requirements: Dockerfiles para django-api y auth-service

## Purpose

Contenerizar los dos servicios del proyecto para que puedan ejecutarse de forma reproducible en cualquier entorno (desarrollo, CI, producción) sin depender de configuración local del host.

- `django-api`: imagen Python/Gunicorn que sirve la API REST.
- `auth-service`: imagen Java multi-stage que compila el proyecto con Maven y produce una imagen de runtime ligera.

## Scope

- **In scope:**
  - `Dockerfile` en `django-api/`
  - `Dockerfile` en `auth-service/`
  - `.dockerignore` para cada servicio
  - Usuario no-root en ambas imágenes
  - Build multi-stage para `auth-service`
  - Workers de Gunicorn configurables via variable de entorno

- **Out of scope:**
  - `docker-compose.yml` (fase 3 del roadmap, tarea separada)
  - Configuración de Nginx (fase 3)
  - Imágenes para entorno de testing o CI
  - Push a registry (Docker Hub, ECR, etc.)
  - Health checks de Docker (se definen en compose/k8s)

---

## Requirements

### django-api

1. La imagen base es `python:3.13-slim` (la versión Python del proyecto es 3.13).
2. El `WORKDIR` es `/app`.
3. Se copian e instalan las dependencias desde `requirements/requirements.txt` **antes** de copiar el código fuente, para aprovechar el cache de capas de Docker.
4. Se copia el contenido de `app/` (donde reside `manage.py` y todos los paquetes) al `WORKDIR`.
5. El servidor arranca con Gunicorn usando `config.wsgi:application` enlazado a `0.0.0.0:8000`.
6. El número de workers de Gunicorn es configurable via la variable de entorno `GUNICORN_WORKERS`. Si no se define, el valor por defecto es `2`.
7. El proceso corre como usuario no-root. Se crea el usuario del sistema `appuser` en el grupo `appgroup` antes de cambiar de usuario.
8. Se expone el puerto `8000`.
9. El `.dockerignore` excluye: `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `mutants/`, `.env`, `.env.*`, `tests/`.

### auth-service

10. El `Dockerfile` usa un build multi-stage con dos stages: `builder` y el stage de runtime final.
11. El stage `builder` usa la imagen `maven:3.9-eclipse-temurin-17`.
12. En el stage `builder`, se copia `pom.xml` primero y se ejecuta `mvn dependency:go-offline` para cachear dependencias antes de copiar el código fuente.
13. El build se ejecuta con `mvn package -DskipTests` (los tests corren en CI, no en el build de la imagen).
14. El stage de runtime usa `eclipse-temurin:17-jre-alpine` (imagen ligera sin JDK).
15. El `.jar` producido en el stage `builder` (`/app/target/auth-service-*.jar`) se copia al stage de runtime como `app.jar`.
16. El proceso corre como usuario no-root. En Alpine, se usa `addgroup -S appgroup && adduser -S appuser -G appgroup` antes de cambiar de usuario.
17. El `ENTRYPOINT` es `["java", "-jar", "app.jar"]`.
18. Se expone el puerto `8080`.
19. El `.dockerignore` excluye: `target/`, `.mvn/wrapper/maven-wrapper.jar` no (sí se necesita el wrapper), `src/test/`, `.env`, `.env.*`.

---

## Scenarios

### Django — imagen construida sin entorno local

- GIVEN que el desarrollador está en una máquina sin Python ni virtualenv instalado
- WHEN ejecuta `docker build -t django-api .` desde `django-api/`
- THEN la imagen se construye satisfactoriamente y el contenedor responde en el puerto 8000

### Django — workers configurables

- GIVEN un contenedor corriendo la imagen `django-api`
- WHEN se lanza con `-e GUNICORN_WORKERS=4`
- THEN Gunicorn arranca con exactamente 4 workers

### Django — workers por defecto

- GIVEN un contenedor corriendo la imagen `django-api`
- WHEN se lanza sin definir `GUNICORN_WORKERS`
- THEN Gunicorn arranca con 2 workers

### auth-service — multi-stage no requiere Maven en el host

- GIVEN que el desarrollador no tiene Maven instalado localmente
- WHEN ejecuta `docker build -t auth-service .` desde `auth-service/`
- THEN Maven descarga dependencias, compila, y la imagen final solo contiene el JRE y el `.jar`

### auth-service — imagen final no incluye fuentes

- GIVEN la imagen `auth-service` construida
- WHEN se inspecciona el sistema de archivos del contenedor
- THEN no existe código fuente Java ni el directorio `src/` — solo `/app/app.jar`

### Seguridad — proceso no-root en ambos servicios

- GIVEN un contenedor corriendo con la imagen de cualquiera de los dos servicios
- WHEN se ejecuta `whoami` dentro del contenedor
- THEN el resultado es `appuser`, no `root`

### Cache de capas — reinstalación evitada

- GIVEN una imagen `django-api` ya construida
- WHEN se modifica un archivo `.py` del código fuente y se vuelve a hacer `docker build`
- THEN el step `pip install` no se re-ejecuta (la capa de dependencias está cacheada)

### Cache de capas Maven — dependencias cacheadas

- GIVEN una imagen `auth-service` ya construida
- WHEN se modifica un archivo `.java` y se vuelve a hacer `docker build`
- THEN el step `mvn dependency:go-offline` no se re-ejecuta
