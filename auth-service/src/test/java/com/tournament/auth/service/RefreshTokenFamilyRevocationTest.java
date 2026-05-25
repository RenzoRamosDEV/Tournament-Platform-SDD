package com.tournament.auth.service;

import com.tournament.auth.domain.RefreshToken;
import com.tournament.auth.domain.User;
import com.tournament.auth.exception.InvalidRefreshTokenException;
import com.tournament.auth.repository.RefreshTokenRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RefreshTokenFamilyRevocationTest {

    @Mock RefreshTokenRepository refreshTokenRepository;
    @Mock JwtService jwtService;

    RefreshTokenService service;

    @BeforeEach
    void setUp() {
        service = new RefreshTokenService(refreshTokenRepository, jwtService, 7L, 900L);
    }

    private User makeUser() {
        User user = new User();
        user.setId(UUID.randomUUID());
        user.setEmail("user@example.com");
        user.setRole("player");
        return user;
    }

    @Test
    void createRefreshToken_storesTokenHash_notRawToken() {
        User user = makeUser();
        UUID familyId = UUID.randomUUID();
        RefreshToken saved = new RefreshToken();
        saved.setFamilyId(familyId);
        saved.setExpiresAt(LocalDateTime.now().plusDays(7));
        when(refreshTokenRepository.save(any(RefreshToken.class))).thenReturn(saved);

        String rawToken = service.createRefreshToken(user);

        ArgumentCaptor<RefreshToken> captor = ArgumentCaptor.forClass(RefreshToken.class);
        verify(refreshTokenRepository).save(captor.capture());
        RefreshToken persisted = captor.getValue();
        assertThat(persisted.getTokenHash()).isNotNull();
        assertThat(rawToken).isNotNull();
        assertThat(rawToken).isNotEqualTo(persisted.getTokenHash());
    }

    @Test
    void rotate_revokedToken_revokesWholeFamily() {
        User user = makeUser();
        UUID familyId = UUID.randomUUID();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = com.tournament.auth.service.HashUtil.sha256(rawToken);

        RefreshToken revoked = new RefreshToken();
        revoked.setTokenHash(tokenHash);
        revoked.setFamilyId(familyId);
        revoked.setUser(user);
        revoked.setExpiresAt(LocalDateTime.now().plusDays(7));
        revoked.setRevoked(true);

        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(revoked));

        assertThatThrownBy(() -> service.rotate(rawToken))
                .isInstanceOf(InvalidRefreshTokenException.class);

        verify(refreshTokenRepository).revokeAllByFamilyId(familyId);
    }

    @Test
    void rotate_validToken_lookupsViaHash() {
        User user = makeUser();
        UUID familyId = UUID.randomUUID();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = com.tournament.auth.service.HashUtil.sha256(rawToken);

        RefreshToken existing = new RefreshToken();
        existing.setTokenHash(tokenHash);
        existing.setFamilyId(familyId);
        existing.setUser(user);
        existing.setExpiresAt(LocalDateTime.now().plusDays(7));
        existing.setRevoked(false);

        RefreshToken newToken = new RefreshToken();
        newToken.setFamilyId(familyId);
        newToken.setExpiresAt(LocalDateTime.now().plusDays(7));

        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(existing));
        when(refreshTokenRepository.save(any(RefreshToken.class))).thenReturn(newToken);
        when(jwtService.generateAccessToken(user)).thenReturn("new.access.token");

        service.rotate(rawToken);

        verify(refreshTokenRepository).findByTokenHash(tokenHash);
        verify(refreshTokenRepository).revokeByTokenHash(tokenHash);
    }
}
