package se.dmolinsky.whattowatchnextbackend.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    private final JdbcTemplate jdbcTemplate;

    public HealthController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping("/api/health")
    public Map<String, Object> health() {
        Integer one = jdbcTemplate.queryForObject("SELECT 1", Integer.class);

        Boolean hasVector = jdbcTemplate.queryForObject(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')",
                Boolean.class
        );

        return Map.of(
                "status", "ok",
                "db", one,
                "pgvector", Boolean.TRUE.equals(hasVector)
        );
    }
}
