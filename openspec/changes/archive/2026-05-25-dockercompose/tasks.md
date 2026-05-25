## 1. Estructura de archivos

- [x] 1.1 Crear el directorio `nginx/` en la raíz del proyecto
- [x] 1.2 Añadir `.env` a `.gitignore` (si no está ya)

## 2. nginx/nginx.conf

- [x] 2.1 Crear `nginx/nginx.conf` con bloque `upstream` o `proxy_pass` directo hacia `django-api:8000` para el prefijo `/api/`
- [x] 2.2 Añadir regla `proxy_pass` hacia `java-auth:8080` para el prefijo `/auth/`
- [x] 2.3 Añadir bloque `location /` que retorne 404 para rutas no reconocidas

## 3. .env.example

- [x] 3.1 Crear `.env.example` con todas las variables requeridas: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST=postgres`, `DB_PORT=5432`, `AUTH_SERVICE_URL=http://java-auth:8080`, `CORS_ALLOWED_ORIGINS`, `JWT_SECRET`, `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `KAFKA_BROKER_ID=1`

## 4. docker-compose.yml

- [x] 4.1 Crear `docker-compose.yml` con la definición de red `app-network` (driver: bridge) y volumen `postgres_data`
- [x] 4.2 Añadir servicio `postgres` con imagen `postgres:15`, volumen `postgres_data`, variables de entorno desde `.env` y healthcheck (`pg_isready -U ${POSTGRES_USER}`, interval 10s, timeout 5s, retries 5)
- [x] 4.3 Añadir servicio `redis` con imagen `redis:7-alpine` y healthcheck (`redis-cli ping`, interval 10s, timeout 5s, retries 5)
- [x] 4.4 Añadir servicio `zookeeper` con imagen `confluentinc/cp-zookeeper`, variables `ZOOKEEPER_CLIENT_PORT=2181` y `ZOOKEEPER_TICK_TIME=2000`
- [x] 4.5 Añadir servicio `kafka` con imagen `confluentinc/cp-kafka`, variables `KAFKA_BROKER_ID`, `KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181`, `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092`, `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1` y healthcheck (`kafka-topics --bootstrap-server localhost:9092 --list`, interval 15s, timeout 10s, retries 10)
- [x] 4.6 Añadir servicio `django-api` con build desde `./django-api`, variables de entorno Django desde `.env`, `depends_on: postgres: condition: service_healthy`
- [x] 4.7 Añadir servicio `java-auth` con build desde `./auth-service`, variables de entorno Spring desde `.env`, `depends_on: postgres: condition: service_healthy`
- [x] 4.8 Añadir servicio `nginx` con imagen `nginx:alpine`, puerto `80:80`, mount de `./nginx/nginx.conf`, `depends_on: django-api: condition: service_started` y `java-auth: condition: service_started`
- [x] 4.9 Verificar que todos los servicios tienen `restart: unless-stopped` y están en `app-network`

## 5. Verificación

- [x] 5.1 Ejecutar `grep -iE "password|secret" docker-compose.yml` — debe retornar vacío
- [x] 5.2 Ejecutar `docker compose config` para validar la sintaxis del compose sin errores
- [x] 5.3 Ejecutar `docker compose up -d` y verificar que todos los servicios alcanzan estado `running` o `healthy`
- [x] 5.4 Verificar que `curl http://localhost/api/tournaments/` retorna HTTP 200 o 401 (no 502)
- [x] 5.5 Verificar que `curl -X POST http://localhost/auth/login` retorna HTTP 400 o 401 (no 502)
- [x] 5.6 Verificar que `curl http://localhost/unknown` retorna HTTP 404
