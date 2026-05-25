## ADDED Requirements

### Requirement: Red interna app-network
Todos los servicios SHALL estar conectados a una red bridge llamada `app-network` definida en `docker-compose.yml`. Los servicios SHALL poder comunicarse entre sí usando el nombre del servicio como hostname.

#### Scenario: Servicios se resuelven por nombre
- **WHEN** el stack está corriendo y se ejecuta `docker compose exec django-api ping -c1 postgres`
- **THEN** la resolución DNS retorna la IP del contenedor `postgres`

---

### Requirement: Volumen persistente para PostgreSQL
SHALL existir un volumen nombrado `postgres_data` montado en `/var/lib/postgresql/data` del servicio `postgres`.

#### Scenario: Datos persisten tras docker compose down / up
- **WHEN** se ejecuta `docker compose down` seguido de `docker compose up -d`
- **THEN** los datos de PostgreSQL siguen disponibles (el volumen no fue eliminado)

#### Scenario: Volumen no eliminado por down sin -v
- **WHEN** se ejecuta `docker compose down` (sin flag `-v`)
- **THEN** `docker volume ls` sigue mostrando el volumen `postgres_data`

---

### Requirement: Credenciales solo en .env
El `docker-compose.yml` NO SHALL contener contraseñas, secrets ni usuarios hardcodeados. Todos los valores sensibles SHALL referenciarse via `${VARIABLE}`.

#### Scenario: Sin credenciales en docker-compose.yml
- **WHEN** se ejecuta `grep -iE "password|secret" docker-compose.yml`
- **THEN** el output está vacío

---

### Requirement: .env.example como plantilla completa
SHALL existir `.env.example` en la raíz con todas las variables requeridas por el compose, con valores de ejemplo (no reales).

#### Scenario: .env.example cubre todas las variables
- **WHEN** un desarrollador copia `.env.example` a `.env`, rellena los valores y ejecuta `docker compose up -d`
- **THEN** el stack arranca sin errores de variables faltantes (`variable is not set`)

---

### Requirement: .env ignorado por git
El archivo `.env` SHALL estar listado en `.gitignore`.

#### Scenario: .env no aparece en git status
- **WHEN** existe un archivo `.env` en la raíz y se ejecuta `git status`
- **THEN** `.env` no aparece como untracked ni staged

---

### Requirement: Servicio postgres con healthcheck
El servicio `postgres` SHALL tener un healthcheck que ejecute `pg_isready -U ${POSTGRES_USER}` con `interval: 10s`, `timeout: 5s`, `retries: 5`.

#### Scenario: postgres marca service_healthy antes de que django-api arranque
- **WHEN** se ejecuta `docker compose up -d`
- **THEN** el contenedor `django-api` no inicia hasta que `postgres` tiene estado `healthy`

---

### Requirement: Servicio redis con healthcheck
El servicio `redis` SHALL usar `redis:7-alpine` y tener un healthcheck con `redis-cli ping`, `interval: 10s`, `timeout: 5s`, `retries: 5`.

#### Scenario: Redis healthcheck pasa
- **WHEN** el contenedor redis está corriendo
- **THEN** `docker inspect --format='{{.State.Health.Status}}' <redis-container>` retorna `healthy`

---

### Requirement: Servicio kafka con healthcheck
El servicio `kafka` SHALL tener un healthcheck que ejecute `kafka-topics --bootstrap-server localhost:9092 --list` con `interval: 15s`, `timeout: 10s`, `retries: 10`.

#### Scenario: Kafka healthcheck pasa tras arranque
- **WHEN** el contenedor kafka ha terminado de inicializar (puede tomar hasta 150s)
- **THEN** `docker inspect` muestra estado `healthy` para kafka

---

### Requirement: django-api depende de postgres healthy
El servicio `django-api` SHALL declarar `depends_on` con `condition: service_healthy` para `postgres`.

#### Scenario: django-api espera a postgres
- **WHEN** se ejecuta `docker compose up -d` desde cero
- **THEN** el proceso de `django-api` no arranca hasta que postgres reporta `healthy`

---

### Requirement: java-auth depende de postgres healthy
El servicio `java-auth` SHALL declarar `depends_on` con `condition: service_healthy` para `postgres`.

#### Scenario: java-auth espera a postgres
- **WHEN** se ejecuta `docker compose up -d` desde cero
- **THEN** el proceso de `java-auth` no arranca hasta que postgres reporta `healthy`

---

### Requirement: restart unless-stopped en todos los servicios
Todos los servicios SHALL tener `restart: unless-stopped`.

#### Scenario: Servicio reinicia tras crash
- **WHEN** el proceso de un servicio termina inesperadamente (exit code != 0)
- **THEN** Docker reinicia automáticamente el contenedor
