package com.tournament.auth.repository;

import com.tournament.auth.domain.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, UUID> {
    Optional<RefreshToken> findByTokenHash(String tokenHash);

    List<RefreshToken> findAllByFamilyId(UUID familyId);

    @Modifying(clearAutomatically = true)
    @Query("UPDATE RefreshToken rt SET rt.revoked = true WHERE rt.tokenHash = :tokenHash")
    void revokeByTokenHash(String tokenHash);

    @Modifying(clearAutomatically = true)
    @Query("UPDATE RefreshToken rt SET rt.revoked = true WHERE rt.familyId = :familyId")
    void revokeAllByFamilyId(UUID familyId);

    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.expiresAt < :cutoff")
    void deleteByExpiresAtBefore(LocalDateTime cutoff);
}
