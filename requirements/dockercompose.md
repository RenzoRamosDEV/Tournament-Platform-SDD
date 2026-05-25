# Requirements: Docker Compose — Orquestación del stack completo

## Purpose

Permitir levantar todo el stack de la plataforma con un solo comando (`docker compose up`), garantizando que los servicios arrancan en el orden correcto, se comunican por nombre de servicio y no exponen credenciales en el repositorio.

## Scope

- **In scope:**
  - `docker-compose.yml` en la raíz del proyecto
  - Red interna `app-network`
  - Volumen persistente para PostgreSQL
  - Healthchecks para postgres, redis y kafka
  - Dependencias ordenadas con `depends_on: condition: service_healthy`
  - Archivo `.env.example` con todas las variables requeridas (valores de ejemplo, sin secretos reales)
  - Entrada en `.gitignore` para `.env`
  - Configuración de Nginx como reverse proxy hacia `django-api` y `java-auth`
  - Archivo `nginx/nginx.conf` con las reglas de proxy

- **Out of scope:**
  - Despliegue en producción o Kubernetes (fase 7)
  - TLS/HTTPS en Nginx (fase posterior)
  - Réplicas o escalado horizontal
  - Profiles de Docker Compose por entorno
  - Push de imágenes a un registry

---

## Requirements

### Red y volúmenes

1. Todos los servicios SHALL estar conectados a una red bridge llamada `app-network` definida en el `docker-compose.yml`.
2. Los servicios SHALL comunicarse entre sí usando el nombre del servicio como hostname (e.g., `postgres`, `kafka`, `django-api`).
3. SHALL existir un volumen nombrado llamado `postgres_data` montado en `/var/lib/postgresql/data` del servicio `postgres`, de modo que los datos persistan entre reinicios y recreaciones del contenedor.

### Credenciales y variables de entorno

4. El archivo `docker-compose.yml` NO SHALL contener ningún valor de credencial hardcodeado (contraseñas, secretos, usuarios). Todos los valores sensibles SHALL ser referenciados via `${VARIABLE}` desde un archivo `.env`.
5. SHALL existir un archivo `.env.example` en la raíz del proyecto con todas las variables requeridas por el compose, con valores de ejemplo seguros (no reales). Sirve como plantilla para que cualquier desarrollador cree su propio `.env`.
6. El archivo `.env` SHALL estar listado en `.gitignore` para que nunca sea commiteado al repositorio.

### Servicios — definición

7. El servicio `postgres` SHALL usar la imagen `postgres:15`, exponer el puerto `5432` únicamente en la red interna (sin publicar al host), y leer `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` desde el `.env`.

8. El servicio `redis` SHALL usar la imagen `redis:7-alpine` y exponer el puerto `6379` únicamente en la red interna.

9. El servicio `zookeeper` SHALL usar la imagen `confluentinc/cp-zookeeper` y exponer el puerto `2181` únicamente en la red interna. SHALL recibir `ZOOKEEPER_CLIENT_PORT=2181` y `ZOOKEEPER_TICK_TIME=2000`.

10. El servicio `kafka` SHALL usar la imagen `confluentinc/cp-kafka` y exponer el puerto `9092` únicamente en la red interna. SHALL configurar `KAFKA_BROKER_ID`, `KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181`, `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092` y `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1`.

11. El servicio `django-api` SHALL construirse desde `./django-api` (usando el `Dockerfile` existente) y exponer el puerto `8000` únicamente en la red interna. SHALL recibir todas las variables de entorno necesarias para Django (SECRET_KEY, DB_*, AUTH_SERVICE_URL, CORS_ALLOWED_ORIGINS) desde el `.env`.

12. El servicio `java-auth` (nombre del servicio en compose) SHALL construirse desde `./auth-service` y exponer el puerto `8080` únicamente en la red interna. SHALL recibir `JWT_SECRET`, `SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/${DB_NAME}`, `SPRING_DATASOURCE_USERNAME` y `SPRING_DATASOURCE_PASSWORD` desde el `.env`.

13. El servicio `nginx` SHALL usar la imagen `nginx:alpine`, ser el **único servicio que publica un puerto al host** (`80:80`), y montar el archivo `./nginx/nginx.conf` como `/etc/nginx/nginx.conf`.

### Nginx — configuración de proxy

14. `nginx.conf` SHALL redirigir las peticiones con prefijo `/api/` hacia `http://django-api:8000/` (strip del prefijo `/api`).
15. `nginx.conf` SHALL redirigir las peticiones con prefijo `/auth/` hacia `http://java-auth:8080/` (strip del prefijo `/auth`).
16. Las peticiones a `/` sin prefijo reconocido SHALL retornar HTTP 404.

### Healthchecks y orden de arranque

17. El servicio `postgres` SHALL tener un healthcheck que ejecute `pg_isready -U ${POSTGRES_USER}` cada 10 segundos, con timeout de 5 segundos y 5 reintentos antes de marcar el servicio como `unhealthy`.

18. El servicio `redis` SHALL tener un healthcheck que ejecute `redis-cli ping` cada 10 segundos, con timeout de 5 segundos y 5 reintentos.

19. El servicio `kafka` SHALL tener un healthcheck que verifique que el broker está listo usando `kafka-topics --bootstrap-server localhost:9092 --list` cada 15 segundos, con timeout de 10 segundos y 10 reintentos (Kafka tarda más en arrancar).

20. El servicio `django-api` SHALL declarar `depends_on` con `condition: service_healthy` para `postgres`. No depende de kafka ni redis directamente (los usará en fases posteriores).

21. El servicio `java-auth` SHALL declarar `depends_on` con `condition: service_healthy` para `postgres`.

22. El servicio `nginx` SHALL declarar `depends_on` (sin healthcheck, solo `service_started`) para `django-api` y `java-auth`.

23. Todos los servicios SHALL tener `restart: unless-stopped`.

---

## Scenarios

### Stack arranca en orden correcto

- GIVEN que no hay contenedores corriendo
- WHEN se ejecuta `docker compose up -d`
- THEN postgres arranca primero; django-api y java-auth arrancan solo después de que postgres responde `pg_isready`; nginx arranca último

### Nginx enruta correctamente a django-api

- GIVEN el stack corriendo con `docker compose up -d`
- WHEN se hace `curl http://localhost/api/tournaments/`
- THEN nginx proxea la petición a `django-api:8000/tournaments/` y retorna una respuesta HTTP (200 o 401, no 502)

### Nginx enruta correctamente a java-auth

- GIVEN el stack corriendo con `docker compose up -d`
- WHEN se hace `curl -X POST http://localhost/auth/login` con body JSON
- THEN nginx proxea la petición a `java-auth:8080/login` y retorna una respuesta HTTP (200 o 401, no 502)

### Datos de PostgreSQL persisten tras reinicio

- GIVEN el stack corriendo con datos en la base de datos
- WHEN se ejecuta `docker compose down` seguido de `docker compose up -d`
- THEN los datos de PostgreSQL están disponibles (el volumen `postgres_data` no fue eliminado)

### .env no es commiteado al repositorio

- GIVEN un repositorio git con el proyecto
- WHEN se ejecuta `git status` teniendo un archivo `.env` en la raíz
- THEN `.env` aparece como "ignored" y no como "untracked" ni "staged"

### Credenciales no presentes en docker-compose.yml

- GIVEN el archivo `docker-compose.yml`
- WHEN se hace `grep -E "password|secret|Password|SECRET" docker-compose.yml`
- THEN el output está vacío (ningún valor de credencial hardcodeado)

### .env.example sirve como plantilla completa

- GIVEN un desarrollador nuevo que clona el repositorio
- WHEN copia `.env.example` a `.env` y reemplaza los valores de ejemplo por valores reales
- THEN `docker compose up -d` arranca el stack sin errores de variables faltantes
