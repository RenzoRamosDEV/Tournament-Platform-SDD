package com.tournament.auth.service;

import com.tournament.auth.domain.RefreshToken;
import com.tournament.auth.domain.User;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class RefreshTokenEntityTest {

    @Test
    void refreshTokenHasRequiredFields() {
        User user = new User();
        user.setId(UUID.randomUUID());

        String tokenHash = "abc123hash";
        UUID familyId = UUID.randomUUID();
        LocalDateTime expiresAt = LocalDateTime.now().plusDays(7);

        RefreshToken rt = new RefreshToken();
        rt.setUser(user);
        rt.setTokenHash(tokenHash);
        rt.setFamilyId(familyId);
        rt.setExpiresAt(expiresAt);
        rt.setRevoked(false);

        assertThat(rt.getUser()).isEqualTo(user);
        assertThat(rt.getTokenHash()).isEqualTo(tokenHash);
        assertThat(rt.getFamilyId()).isEqualTo(familyId);
        assertThat(rt.getExpiresAt()).isEqualTo(expiresAt);
        assertThat(rt.isRevoked()).isFalse();
    }

    @Test
    void isExpiredReturnsTrueWhenExpiresAtIsInThePast() {
        RefreshToken rt = new RefreshToken();
        rt.setExpiresAt(LocalDateTime.now().minusSeconds(1));
        assertThat(rt.isExpired()).isTrue();
    }

    @Test
    void isExpiredReturnsFalseWhenExpiresAtIsInTheFuture() {
        RefreshToken rt = new RefreshToken();
        rt.setExpiresAt(LocalDateTime.now().plusDays(1));
        assertThat(rt.isExpired()).isFalse();
    }
}
