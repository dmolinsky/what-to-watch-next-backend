package se.dmolinsky.whattowatchnextbackend.security;

import io.github.bucket4j.Bucket;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Refill;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

    private Bucket newBucketForPath(String path) {
        // Tune these as you like:
        // recommendations are expensive -> stricter
        Bandwidth limit = path.contains("/recommendations")
                ? Bandwidth.classic(30, Refill.greedy(30, Duration.ofMinutes(1)))   // 30/min
                : Bandwidth.classic(120, Refill.greedy(120, Duration.ofMinutes(1))); // 120/min

        return Bucket4j.builder().addLimit(limit).build();
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {

        String ip = request.getRemoteAddr();
        String path = request.getRequestURI();

        // only rate limit your API routes
        if (!path.startsWith("/api/")) {
            chain.doFilter(request, response);
            return;
        }

        String key = ip + ":" + (path.contains("/recommendations") ? "recs" : "api");
        Bucket bucket = buckets.computeIfAbsent(key, k -> newBucketForPath(path));

        if (bucket.tryConsume(1)) {
            chain.doFilter(request, response);
            return;
        }

        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value()); // 429
        response.setContentType("application/json");
        response.getWriter().write("""
                {"error":"too_many_requests","message":"Rate limit exceeded"}
                """);
    }
}
