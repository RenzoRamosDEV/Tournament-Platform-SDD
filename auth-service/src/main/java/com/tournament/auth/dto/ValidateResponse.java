package com.tournament.auth.dto;

public record ValidateResponse(boolean valid, String email, String role) {
    public static ValidateResponse invalid() {
        return new ValidateResponse(false, null, null);
    }
}
