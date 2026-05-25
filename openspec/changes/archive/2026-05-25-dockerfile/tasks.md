## 1. django-api Dockerfile

- [x] 1.1 Crear `django-api/Dockerfile` con imagen base `python:3.13-slim`, WORKDIR `/app` y usuario no-root `appuser`
- [x] 1.2 Añadir step de instalación de dependencias desde `requirements/requirements.txt` antes de copiar el código fuente
- [x] 1.3 Añadir step `COPY app/ .` para copiar el código fuente al WORKDIR
- [x] 1.4 Añadir `EXPOSE 8000` y `CMD` con Gunicorn usando `${GUNICORN_WORKERS:-2}` workers

## 2. django-api .dockerignore

- [x] 2.1 Crear `django-api/.dockerignore` excluyendo `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `mutants/`, `.env`, `.env.*`, `tests/`

## 3. auth-service Dockerfile

- [x] 3.1 Crear `auth-service/Dockerfile` con stage `builder` usando `maven:3.9-eclipse-temurin-17`
- [x] 3.2 En el stage `builder`: copiar `pom.xml`, ejecutar `mvn dependency:go-offline`, luego copiar `src/` y ejecutar `mvn package -DskipTests`
- [x] 3.3 Añadir stage de runtime con `eclipse-temurin:17-jre-alpine`, copiar el `.jar` como `/app/app.jar`
- [x] 3.4 Crear usuario no-root `appuser` en el stage de runtime y añadir `EXPOSE 8080` + `ENTRYPOINT ["java", "-jar", "app.jar"]`

## 4. auth-service .dockerignore

- [x] 4.1 Crear `auth-service/.dockerignore` excluyendo `target/`, `.env`, `.env.*`

## 5. Verificación

- [x] 5.1 Ejecutar `docker build -t django-api ./django-api` y verificar que la imagen se construye sin errores
- [x] 5.2 Verificar proceso no-root: `docker run --rm django-api whoami` → `appuser`
- [x] 5.3 Verificar workers por defecto: `docker run --rm django-api sh -c 'gunicorn --check-config config.wsgi:application'` (o revisar logs de inicio)
- [x] 5.4 Ejecutar `docker build -t auth-service ./auth-service` y verificar que la imagen se construye sin errores
- [x] 5.5 Verificar proceso no-root: `docker run --rm --entrypoint whoami auth-service` → `appuser`
- [x] 5.6 Verificar que la imagen final de auth-service no contiene `src/`: `docker run --rm auth-service ls /app` → solo `app.jar`
