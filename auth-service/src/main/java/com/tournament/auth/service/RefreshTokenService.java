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

    public RefreshTokenService(RefreshTokenRepository refreshTokenRepository,
                               JwtService jwtService,
                               @Value("${jwt.refresh-token-expiration-days:7}") long refreshTokenExpirationDays) {
        this.refreshTokenRepository = refreshTokenRepository;
        this.jwtService = jwtService;
        this.refreshTokenExpirationDays = refreshTokenExpirationDays;
    }

    public RefreshToken createRefreshToken(User user) {
        RefreshToken rt = new RefreshToken();
        rt.setUser(user);
        rt.setToken(UUID.randomUUID());
        rt.setExpiresAt(LocalDateTime.now().plusDays(refreshTokenExpirationDays));
        rt.setRevoked(false);
        return refreshTokenRepository.save(rt);
    }

    @Transactional
    public LoginResponse rotate(String tokenString) {
        UUID tokenUuid;
        try {
            tokenUuid = UUID.fromString(tokenString);
        } catch (IllegalArgumentException e) {
            throw new InvalidRefreshTokenException();
        }

        RefreshToken existing = refreshTokenRepository.findByToken(tokenUuid)
                .orElseThrow(InvalidRefreshTokenException::new);

        if (existing.isRevoked() || existing.isExpired()) {
            throw new InvalidRefreshTokenException();
        }

        refreshTokenRepository.revokeByToken(tokenUuid);

        User user = existing.getUser();
        RefreshToken newToken = createRefreshToken(user);
        String accessToken = jwtService.generateAccessToken(user);

        return new LoginResponse(accessToken, newToken.getToken().toString(), "Bearer", 86400);
    }
}
