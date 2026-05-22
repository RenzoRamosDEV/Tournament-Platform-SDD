package com.tournament.auth.config;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class JwtSecretValidator {

    private static final Logger log = LoggerFactory.getLogger(JwtSecretValidator.class);
    private static final int MIN_SECRET_LENGTH = 32;

    private final String secret;

    public JwtSecretValidator(@Value("${jwt.secret:}") String secret) {
        this.secret = secret;
    }

    @PostConstruct
    public void validate() {
        if (secret == null || secret.isBlank()) {
            log.error("FATAL: JWT_SECRET environment variable is required");
            throw new IllegalStateException("FATAL: JWT_SECRET environment variable is required");
        }
        if (secret.length() < MIN_SECRET_LENGTH) {
            log.error("FATAL: JWT_SECRET must be at least 32 characters");
            throw new IllegalStateException("FATAL: JWT_SECRET must be at least 32 characters");
        }
    }
}
