package com.tournament.auth.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tournament.auth.dto.RegisterRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class SecurityConfigTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    @Test
    void register_isAccessibleWithoutAuth() throws Exception {
        var req = new RegisterRequest("sec@example.com", "pass123", "player", "secuser");
        mvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(req)))
                .andExpect(status().isCreated());
    }

    @Test
    void login_isAccessibleWithoutAuth() throws Exception {
        mvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("email", "x@y.com", "password", "p"))))
                .andExpect(status().isUnauthorized()); // 401 from our logic, not Spring Security
    }

    @Test
    void validate_isAccessibleWithoutAuth() throws Exception {
        mvc.perform(post("/auth/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("token", "x.y.z"))))
                .andExpect(status().isOk());
    }

    @Test
    void refresh_isAccessibleWithoutAuth() throws Exception {
        mvc.perform(post("/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("refresh_token", "00000000-0000-0000-0000-000000000000"))))
                .andExpect(status().isUnauthorized()); // 401 from our logic
    }

    @Test
    void unknown_endpoint_returns401_json() throws Exception {
        mvc.perform(get("/api/unknown"))
                .andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));
    }
}
