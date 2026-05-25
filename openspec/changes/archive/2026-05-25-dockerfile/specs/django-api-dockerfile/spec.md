## ADDED Requirements

### Requirement: Imagen base Python correcta
La imagen base del `Dockerfile` de `django-api` SHALL ser `python:3.13-slim`.

#### Scenario: Imagen construida con Python 3.13
- **WHEN** se ejecuta `docker build` en `django-api/`
- **THEN** `docker run --rm django-api python --version` retorna `Python 3.13.x`

---

### Requirement: Dependencias instaladas antes que el código fuente
El `Dockerfile` SHALL copiar `requirements/requirements.txt` e instalar dependencias con `pip install --no-cache-dir` ANTES de copiar el código fuente de `app/`.

#### Scenario: Cache de dependencias preservado al cambiar código
- **WHEN** se modifica un archivo `.py` dentro de `app/` y se vuelve a ejecutar `docker build`
- **THEN** el layer de `pip install` no se re-ejecuta (aparece `CACHED` en el output del build)

---

### Requirement: Código fuente copiado desde app/
El `Dockerfile` SHALL copiar el contenido de `app/` (no de la raíz del contexto) al `WORKDIR /app`, de modo que `manage.py` y todos los paquetes queden en `/app`.

#### Scenario: manage.py accesible en WORKDIR
- **WHEN** se ejecuta `docker run --rm django-api ls /app`
- **THEN** la salida incluye `manage.py`

---

### Requirement: Servidor Gunicorn con workers configurables
El contenedor SHALL arrancar Gunicorn sirviendo `config.wsgi:application` en `0.0.0.0:8000`. El número de workers SHALL leerse de la variable de entorno `GUNICORN_WORKERS`; si no está definida, el valor por defecto SHALL ser `2`.

#### Scenario: Workers por defecto cuando no se define la env var
- **WHEN** se lanza el contenedor sin definir `GUNICORN_WORKERS`
- **THEN** Gunicorn arranca con 2 workers (visible en los logs de inicio)

#### Scenario: Workers configurados via env var
- **WHEN** se lanza el contenedor con `-e GUNICORN_WORKERS=4`
- **THEN** Gunicorn arranca con 4 workers

---

### Requirement: Proceso ejecutado como usuario no-root
El `Dockerfile` SHALL crear el usuario de sistema `appuser` en el grupo `appgroup` y cambiar a ese usuario antes del `CMD`. El proceso Gunicorn SHALL correr como `appuser`.

#### Scenario: Proceso no-root verificado
- **WHEN** se ejecuta `docker run --rm django-api whoami`
- **THEN** la salida es `appuser`

---

### Requirement: .dockerignore excluye archivos innecesarios
El archivo `django-api/.dockerignore` SHALL excluir: `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `mutants/`, `.env`, `.env.*`, `tests/`.

#### Scenario: .venv no incluida en el contexto de build
- **WHEN** se ejecuta `docker build` con `--progress=plain`
- **THEN** el paso `COPY app/ .` no transfiere el directorio `.venv/`

---

### Requirement: Puerto 8000 expuesto
El `Dockerfile` SHALL incluir `EXPOSE 8000`.

#### Scenario: Puerto declarado en la imagen
- **WHEN** se ejecuta `docker inspect django-api`
- **THEN** `Config.ExposedPorts` incluye `8000/tcp`
