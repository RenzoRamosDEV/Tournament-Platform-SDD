package com.tournament.auth.controller;

import com.tournament.auth.dto.*;
import com.tournament.auth.service.JwtService;
import com.tournament.auth.service.RefreshTokenService;
import com.tournament.auth.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final UserService userService;
    private final RefreshTokenService refreshTokenService;
    private final JwtService jwtService;

    public AuthController(UserService userService,
                          RefreshTokenService refreshTokenService,
                          JwtService jwtService) {
        this.userService = userService;
        this.refreshTokenService = refreshTokenService;
        this.jwtService = jwtService;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public RegisterResponse register(@Valid @RequestBody RegisterRequest req) {
        return userService.register(req.email(), req.password(), req.role(), req.username());
    }

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginRequest req) {
        return userService.login(req.email(), req.password());
    }

    @PostMapping("/refresh")
    public LoginResponse refresh(@Valid @RequestBody RefreshRequest req) {
        return refreshTokenService.rotate(req.refreshToken());
    }

    @PostMapping("/validate")
    public ValidateResponse validate(@Valid @RequestBody ValidateRequest req) {
        return jwtService.validate(req.token());
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(@Valid @RequestBody LogoutRequest req) {
        refreshTokenService.logout(req.refreshToken());
        return ResponseEntity.noContent().build();
    }
}
