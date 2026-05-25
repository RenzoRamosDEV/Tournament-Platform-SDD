package com.tournament.auth.service;

import com.tournament.auth.domain.RefreshToken;
import com.tournament.auth.domain.User;
import com.tournament.auth.dto.LoginResponse;
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
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RefreshTokenServiceTest {

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

    private RefreshToken makeActiveToken(User user, String tokenHash) {
        RefreshToken rt = new RefreshToken();
        rt.setTokenHash(tokenHash);
        rt.setFamilyId(UUID.randomUUID());
        rt.setUser(user);
        rt.setExpiresAt(LocalDateTime.now().plusDays(7));
        rt.setRevoked(false);
        return rt;
    }

    // --- createRefreshToken ---

    @Test
    void createRefreshToken_persistsAndReturnsRawToken() {
        User user = makeUser();
        RefreshToken saved = new RefreshToken();
        saved.setFamilyId(UUID.randomUUID());
        saved.setExpiresAt(LocalDateTime.now().plusDays(7));
        when(refreshTokenRepository.save(any(RefreshToken.class))).thenReturn(saved);

        String rawToken = service.createRefreshToken(user);

        assertThat(rawToken).isNotNull();
        ArgumentCaptor<RefreshToken> captor = ArgumentCaptor.forClass(RefreshToken.class);
        verify(refreshTokenRepository).save(captor.capture());
        assertThat(captor.getValue().getTokenHash()).isEqualTo(HashUtil.sha256(rawToken));
    }

    // --- rotate ---

    @Test
    void rotate_validToken_revokesOldAndIssuesNew() {
        User user = makeUser();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);
        RefreshToken existing = makeActiveToken(user, tokenHash);
        RefreshToken newSaved = new RefreshToken();
        newSaved.setFamilyId(existing.getFamilyId());
        newSaved.setExpiresAt(LocalDateTime.now().plusDays(7));

        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(existing));
        when(refreshTokenRepository.save(any(RefreshToken.class))).thenReturn(newSaved);
        when(jwtService.generateAccessToken(user)).thenReturn("new.access.token");

        LoginResponse resp = service.rotate(rawToken);

        verify(refreshTokenRepository).revokeByTokenHash(tokenHash);
        assertThat(resp.accessToken()).isEqualTo("new.access.token");
        assertThat(resp.tokenType()).isEqualTo("Bearer");
    }

    @Test
    void rotate_unknownToken_throwsInvalidRefreshToken() {
        String rawToken = UUID.randomUUID().toString();
        when(refreshTokenRepository.findByTokenHash(anyString())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.rotate(rawToken))
                .isInstanceOf(InvalidRefreshTokenException.class);
    }

    @Test
    void rotate_revokedToken_throwsInvalidRefreshToken() {
        User user = makeUser();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);
        RefreshToken revoked = makeActiveToken(user, tokenHash);
        revoked.setRevoked(true);
        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(revoked));

        assertThatThrownBy(() -> service.rotate(rawToken))
                .isInstanceOf(InvalidRefreshTokenException.class);
    }

    @Test
    void rotate_expiredToken_throwsInvalidRefreshToken() {
        User user = makeUser();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);
        RefreshToken expired = makeActiveToken(user, tokenHash);
        expired.setExpiresAt(LocalDateTime.now().minusSeconds(1));
        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(expired));

        assertThatThrownBy(() -> service.rotate(rawToken))
                .isInstanceOf(InvalidRefreshTokenException.class);
    }

    // --- logout ---

    @Test
    void logout_validToken_revokesIt() {
        User user = makeUser();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);
        RefreshToken rt = makeActiveToken(user, tokenHash);
        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(rt));

        service.logout(rawToken);

        verify(refreshTokenRepository).revokeByTokenHash(tokenHash);
    }

    @Test
    void logout_revokedToken_throwsInvalidRefreshToken() {
        User user = makeUser();
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);
        RefreshToken revoked = makeActiveToken(user, tokenHash);
        revoked.setRevoked(true);
        when(refreshTokenRepository.findByTokenHash(tokenHash)).thenReturn(Optional.of(revoked));

        assertThatThrownBy(() -> service.logout(rawToken))
                .isInstanceOf(InvalidRefreshTokenException.class);
    }
}
