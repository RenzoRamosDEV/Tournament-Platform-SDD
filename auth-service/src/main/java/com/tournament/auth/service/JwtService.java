package com.tournament.auth.service;

import com.tournament.auth.domain.User;
import com.tournament.auth.dto.ValidateResponse;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

@Service
public class JwtService {

    private final SecretKey key;
    private final long accessTokenExpirationSeconds;

    public JwtService(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.access-token-expiration-seconds:900}") long accessTokenExpirationSeconds) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessTokenExpirationSeconds = accessTokenExpirationSeconds;
    }

    public String generateAccessToken(User user) {
        long nowMs = System.currentTimeMillis();
        return Jwts.builder()
                .subject(user.getEmail())
                .claim("role", user.getRole())
                .issuedAt(new Date(nowMs))
                .expiration(new Date(nowMs + accessTokenExpirationSeconds * 1000))
                .signWith(key)
                .compact();
    }

    public ValidateResponse validate(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(key)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            return new ValidateResponse(true, claims.getSubject(), claims.get("role", String.class));
        } catch (JwtException | IllegalArgumentException e) {
            return ValidateResponse.invalid();
        }
    }
}
