package com.tournament.auth.service;

import com.tournament.auth.domain.User;
import com.tournament.auth.dto.LoginResponse;
import com.tournament.auth.dto.RegisterResponse;
import com.tournament.auth.exception.EmailAlreadyExistsException;
import com.tournament.auth.exception.InvalidCredentialsException;
import com.tournament.auth.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock UserRepository userRepository;
    @Mock PasswordEncoder passwordEncoder;
    @Mock JwtService jwtService;
    @Mock RefreshTokenService refreshTokenService;

    UserService userService;

    @BeforeEach
    void setUp() {
        userService = new UserService(userRepository, passwordEncoder, jwtService, refreshTokenService, 900L);
    }

    // --- register ---

    @Test
    void register_newEmail_persistsAndReturnsResponse() {
        when(userRepository.existsByEmail("new@example.com")).thenReturn(false);
        when(passwordEncoder.encode("secret")).thenReturn("hashed");
        User saved = new User();
        saved.setId(UUID.randomUUID());
        saved.setEmail("new@example.com");
        saved.setRole("player");
        when(userRepository.save(any(User.class))).thenReturn(saved);

        RegisterResponse resp = userService.register("new@example.com", "secret", "player", "newuser");

        assertThat(resp.email()).isEqualTo("new@example.com");
        verify(passwordEncoder).encode("secret");
        verify(userRepository).save(any(User.class));
    }

    @Test
    void register_duplicateEmail_throwsEmailAlreadyExists() {
        when(userRepository.existsByEmail("dup@example.com")).thenReturn(true);

        assertThatThrownBy(() -> userService.register("dup@example.com", "pass", "player", "u"))
                .isInstanceOf(EmailAlreadyExistsException.class);

        verify(userRepository, never()).save(any());
    }

    // --- login ---

    @Test
    void login_validCredentials_returnsTokens() {
        User user = new User();
        user.setId(UUID.randomUUID());
        user.setEmail("user@example.com");
        user.setPassword("hashed");
        user.setRole("player");
        when(userRepository.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("password", "hashed")).thenReturn(true);
        when(jwtService.generateAccessToken(user)).thenReturn("access.token");
        String rawRefreshToken = "some-raw-refresh-token";
        when(refreshTokenService.createRefreshToken(user)).thenReturn(rawRefreshToken);

        LoginResponse resp = userService.login("user@example.com", "password");

        assertThat(resp.accessToken()).isEqualTo("access.token");
        assertThat(resp.refreshToken()).isEqualTo(rawRefreshToken);
        assertThat(resp.tokenType()).isEqualTo("Bearer");
        assertThat(resp.expiresIn()).isEqualTo(900L);
    }

    @Test
    void login_unknownEmail_throwsInvalidCredentials() {
        when(userRepository.findByEmail(anyString())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> userService.login("ghost@example.com", "pass"))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    @Test
    void login_wrongPassword_throwsInvalidCredentials() {
        User user = new User();
        user.setPassword("hashed");
        when(userRepository.findByEmail("u@example.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("wrong", "hashed")).thenReturn(false);

        assertThatThrownBy(() -> userService.login("u@example.com", "wrong"))
                .isInstanceOf(InvalidCredentialsException.class);
    }
}
