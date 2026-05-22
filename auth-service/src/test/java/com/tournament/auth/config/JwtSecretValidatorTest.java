package com.tournament.auth.config;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JwtSecretValidatorTest {

    @Test
    void throwsWhenSecretIsBlank() {
        JwtSecretValidator validator = new JwtSecretValidator("");
        assertThatThrownBy(validator::validate)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("JWT_SECRET environment variable is required");
    }

    @Test
    void throwsWhenSecretIsTooShort() {
        JwtSecretValidator validator = new JwtSecretValidator("short");
        assertThatThrownBy(validator::validate)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("JWT_SECRET must be at least 32 characters");
    }

    @Test
    void passesWhenSecretIsLongEnough() {
        JwtSecretValidator validator = new JwtSecretValidator("a-valid-secret-that-is-32-chars!!!");
        validator.validate();
    }
}
