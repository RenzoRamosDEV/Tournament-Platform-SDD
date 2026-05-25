package com.tournament.auth.integration;

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
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthFlowIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    @Test
    void fullLoginValidateFlow() throws Exception {
        // register
        mvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(
                                new RegisterRequest("flow@example.com", "pass123!", "organizer", "flowuser"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.email").value("flow@example.com"));

        // login
        MvcResult loginResult = mvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(
                                new LoginRequest("flow@example.com", "pass123!"))))
                .andExpect(status().isOk())
                .andReturn();

        Map<?, ?> loginBody = mapper.readValue(loginResult.getResponse().getContentAsString(), Map.class);
        String accessToken = (String) loginBody.get("access_token");

        // validate
        mvc.perform(post("/auth/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("token", accessToken))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.valid").value(true))
                .andExpect(jsonPath("$.email").value("flow@example.com"))
                .andExpect(jsonPath("$.role").value("organizer"));
    }

    @Test
    void refreshTokenRotationAndReuseRejection() throws Exception {
        // register + login
        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(
                        new RegisterRequest("rotate@example.com", "pass123!", "admin", "rotateuser"))));

        MvcResult loginResult = mvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(
                                new LoginRequest("rotate@example.com", "pass123!"))))
                .andReturn();

        Map<?, ?> loginBody = mapper.readValue(loginResult.getResponse().getContentAsString(), Map.class);
        String originalRefreshToken = (String) loginBody.get("refresh_token");

        // first refresh — should succeed and issue new tokens
        MvcResult refreshResult = mvc.perform(post("/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", originalRefreshToken))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.access_token").isNotEmpty())
                .andExpect(jsonPath("$.refresh_token").isNotEmpty())
                .andReturn();

        Map<?, ?> refreshBody = mapper.readValue(refreshResult.getResponse().getContentAsString(), Map.class);
        String newRefreshToken = (String) refreshBody.get("refresh_token");

        // reuse the original (now revoked) token — triggers family revocation
        mvc.perform(post("/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", originalRefreshToken))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("INVALID_REFRESH_TOKEN"));

        // new token should also be revoked due to family revocation
        mvc.perform(post("/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", newRefreshToken))))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("INVALID_REFRESH_TOKEN"));
    }
}
