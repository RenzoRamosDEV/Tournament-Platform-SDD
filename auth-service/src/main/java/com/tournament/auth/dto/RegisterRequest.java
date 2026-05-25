package com.tournament.auth.dto;

import com.tournament.auth.validation.ValidRole;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record RegisterRequest(
        @NotBlank @Email String email,
        @NotBlank String password,
        @NotBlank @ValidRole String role,
        @NotBlank String username
) {}
