package com.tournament.auth.service;

import com.tournament.auth.domain.RefreshToken;
import com.tournament.auth.domain.User;
import com.tournament.auth.dto.LoginResponse;
import com.tournament.auth.exception.InvalidRefreshTokenException;
import com.tournament.auth.repository.RefreshTokenRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class RefreshTokenService {

    private final RefreshTokenRepository refreshTokenRepository;
    private final JwtService jwtService;
    private final long refreshTokenExpirationDays;
    private final long accessTokenExpirationSeconds;

    public RefreshTokenService(RefreshTokenRepository refreshTokenRepository,
                               JwtService jwtService,
                               @Value("${jwt.refresh-token-expiration-days:7}") long refreshTokenExpirationDays,
                               @Value("${jwt.access-token-expiration-seconds:900}") long accessTokenExpirationSeconds) {
        this.refreshTokenRepository = refreshTokenRepository;
        this.jwtService = jwtService;
        this.refreshTokenExpirationDays = refreshTokenExpirationDays;
        this.accessTokenExpirationSeconds = accessTokenExpirationSeconds;
    }

    public String createRefreshToken(User user) {
        return createRefreshToken(user, UUID.randomUUID());
    }

    private String createRefreshToken(User user, UUID familyId) {
        String rawToken = UUID.randomUUID().toString();
        String tokenHash = HashUtil.sha256(rawToken);

        RefreshToken rt = new RefreshToken();
        rt.setUser(user);
        rt.setTokenHash(tokenHash);
        rt.setFamilyId(familyId);
        rt.setExpiresAt(LocalDateTime.now().plusDays(refreshTokenExpirationDays));
        rt.setRevoked(false);
        refreshTokenRepository.save(rt);

        return rawToken;
    }

    @Transactional
    public LoginResponse rotate(String rawToken) {
        String tokenHash = HashUtil.sha256(rawToken);

        RefreshToken existing = refreshTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(InvalidRefreshTokenException::new);

        if (existing.isRevoked()) {
            refreshTokenRepository.revokeAllByFamilyId(existing.getFamilyId());
            throw new InvalidRefreshTokenException();
        }

        if (existing.isExpired()) {
            throw new InvalidRefreshTokenException();
        }

        refreshTokenRepository.revokeByTokenHash(tokenHash);

        User user = existing.getUser();
        String newRawToken = createRefreshToken(user, existing.getFamilyId());
        String accessToken = jwtService.generateAccessToken(user);

        return new LoginResponse(accessToken, newRawToken, "Bearer", accessTokenExpirationSeconds);
    }

    @Transactional
    public void logout(String rawToken) {
        String tokenHash = HashUtil.sha256(rawToken);

        RefreshToken existing = refreshTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(InvalidRefreshTokenException::new);

        if (existing.isRevoked() || existing.isExpired()) {
            throw new InvalidRefreshTokenException();
        }

        refreshTokenRepository.revokeByTokenHash(tokenHash);
    }
}
