## ADDED Requirements

### Requirement: Build multi-stage con Maven y JRE-Alpine
El `Dockerfile` de `auth-service` SHALL usar exactamente dos stages: `builder` (imagen `maven:3.9-eclipse-temurin-17`) y el stage de runtime (imagen `eclipse-temurin:17-jre-alpine`). La imagen final SHALL contener solo el JRE y el `.jar`, sin JDK, Maven ni código fuente.

#### Scenario: Imagen final no contiene código fuente
- **WHEN** se ejecuta `docker run --rm auth-service ls /app`
- **THEN** la salida es únicamente `app.jar` (sin directorio `src/`)

#### Scenario: Build sin Maven en el host
- **WHEN** se ejecuta `docker build -t auth-service .` en una máquina sin Maven instalado
- **THEN** el build completa exitosamente y la imagen se crea

---

### Requirement: Cache de dependencias Maven antes del código fuente
En el stage `builder`, el `Dockerfile` SHALL copiar `pom.xml` y ejecutar `mvn dependency:go-offline` ANTES de copiar `src/`. El build final SHALL ejecutarse con `mvn package -DskipTests`.

#### Scenario: Cache de dependencias Maven preservado al cambiar código
- **WHEN** se modifica un archivo `.java` y se vuelve a ejecutar `docker build`
- **THEN** el step `mvn dependency:go-offline` no se re-ejecuta (aparece `CACHED` en el output del build)

---

### Requirement: JAR copiado al stage de runtime como app.jar
El `.jar` producido por Maven (`/app/target/auth-service-*.jar`) SHALL copiarse al stage de runtime en `/app/app.jar`.

#### Scenario: app.jar accesible en el contenedor de runtime
- **WHEN** se ejecuta `docker run --rm auth-service ls /app`
- **THEN** la salida incluye `app.jar`

---

### Requirement: Entrypoint es java -jar app.jar
El stage de runtime SHALL usar `ENTRYPOINT ["java", "-jar", "app.jar"]` como punto de entrada.

#### Scenario: Contenedor arranca el proceso Java
- **WHEN** se inicia el contenedor `auth-service` con las variables de entorno requeridas (`JWT_SECRET`, datasource)
- **THEN** Spring Boot arranca y el servicio responde en el puerto 8080

---

### Requirement: Proceso ejecutado como usuario no-root
El stage de runtime SHALL crear el usuario de sistema `appuser` en el grupo `appgroup` (usando la sintaxis Alpine: `addgroup -S` / `adduser -S`) y cambiar a ese usuario antes del `ENTRYPOINT`.

#### Scenario: Proceso no-root verificado
- **WHEN** se ejecuta `docker run --rm auth-service whoami`
- **THEN** la salida es `appuser`

---

### Requirement: Puerto 8080 expuesto
El stage de runtime SHALL incluir `EXPOSE 8080`.

#### Scenario: Puerto declarado en la imagen
- **WHEN** se ejecuta `docker inspect auth-service`
- **THEN** `Config.ExposedPorts` incluye `8080/tcp`

---

### Requirement: .dockerignore excluye artefactos de build y entorno
El archivo `auth-service/.dockerignore` SHALL excluir: `target/`, `.env`, `.env.*`. No SHALL excluir `mvnw` ni `.mvn/` (el wrapper es necesario si se usa en otros contextos).

#### Scenario: Directorio target no transferido al contexto de build
- **WHEN** se ejecuta `docker build` con `--progress=plain`
- **THEN** el directorio `target/` no aparece en la transferencia del contexto de build
