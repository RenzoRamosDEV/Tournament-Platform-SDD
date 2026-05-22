package com.tournament.auth.service;

import com.tournament.auth.domain.User;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class UserEntityTest {

    @Test
    void userHasRequiredFields() {
        User user = new User();
        UUID id = UUID.randomUUID();
        user.setId(id);
        user.setEmail("player@example.com");
        user.setUsername("player1");
        user.setPassword("hashed");
        user.setRole("player");

        assertThat(user.getId()).isEqualTo(id);
        assertThat(user.getEmail()).isEqualTo("player@example.com");
        assertThat(user.getUsername()).isEqualTo("player1");
        assertThat(user.getPassword()).isEqualTo("hashed");
        assertThat(user.getRole()).isEqualTo("player");
    }

    @Test
    void roleValuesAreValidSet() {
        assertThat(User.VALID_ROLES).containsExactlyInAnyOrder("admin", "organizer", "player");
    }
}
