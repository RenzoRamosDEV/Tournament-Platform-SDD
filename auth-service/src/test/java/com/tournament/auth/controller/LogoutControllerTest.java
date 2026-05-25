package com.tournament.auth.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tournament.auth.dto.LoginRequest;
import com.tournament.auth.dto.RegisterRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class LogoutControllerTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    private String obtainRefreshToken() throws Exception {
        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(
                        new RegisterRequest("logout@example.com", "pass123", "player", "logoutuser"))));
        var result = mvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(new LoginRequest("logout@example.com", "pass123"))))
                .andReturn();
        return (String) mapper.readValue(result.getResponse().getContentAsString(), Map.class).get("refresh_token");
    }

    @Test
    void logout_validToken_returns204() throws Exception {
        String rt = obtainRefreshToken();
        mvc.perform(post("/auth/logout")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", rt))))
                .andExpect(status().isNoContent());
    }

    @Test
    void logout_preventsSubsequentRefresh() throws Exception {
        String rt = obtainRefreshToken();
        mvc.perform(post("/auth/logout")
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("refresh_token", rt))));

        mvc.perform(post("/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", rt))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("INVALID_REFRESH_TOKEN"));
    }

    @Test
    void logout_unknownToken_returns401() throws Exception {
        mvc.perform(post("/auth/logout")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", UUID.randomUUID().toString()))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("INVALID_REFRESH_TOKEN"));
    }

    @Test
    void logout_alreadyRevokedToken_returns401() throws Exception {
        String rt = obtainRefreshToken();
        // first logout revokes it
        mvc.perform(post("/auth/logout")
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("refresh_token", rt))));
        // second logout should be rejected
        mvc.perform(post("/auth/logout")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", rt))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("INVALID_REFRESH_TOKEN"));
    }

    @Test
    void logout_noAuthHeader_isAccessible() throws Exception {
        String rt = obtainRefreshToken();
        mvc.perform(post("/auth/logout")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", rt))))
                .andExpect(status().isNoContent());
    }
}
