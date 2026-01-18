package se.dmolinsky.whattowatchnextbackend.service;

import io.github.resilience4j.ratelimiter.annotation.RateLimiter;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import se.dmolinsky.whattowatchnextbackend.domain.Title;
import se.dmolinsky.whattowatchnextbackend.dto.RecommendationDto;
import se.dmolinsky.whattowatchnextbackend.repository.TitleRepository;

import java.util.Arrays;
import java.util.List;

@Service
public class RecommendationService {

    private final TitleRepository titleRepository;

    public RecommendationService(TitleRepository titleRepository) {
        this.titleRepository = titleRepository;
    }

    private static List<String> toList(String[] arr) {
        return arr == null ? null : Arrays.asList(arr);
    }

    public List<RecommendationDto> recommendByTitle(String queryTitle, int limit) {
        Title base = titleRepository.findFirstByTitleIgnoreCase(queryTitle)
                .orElseThrow(() -> new NotFoundException("Title not found: " + queryTitle));

        return recommendById(base.getId(), limit);
    }

    @RateLimiter(name = "recommendations")
    @Cacheable(
            value = "recommendations",
            key = "#baseId + ':' + #limit"
    )
    public List<RecommendationDto> recommendById(Integer baseId, int limit) {
        var rows = titleRepository.findRecommendationsByBaseId(baseId, limit);

        if (rows.isEmpty()) {
            throw new NotFoundException("No combined embedding available for title id: " + baseId);
        }

        return rows.stream()
                .map(r -> new RecommendationDto(
                        r.getId(),
                        r.getTitle(),
                        r.getYear(),
                        r.getType(),
                        toList(r.getGenres()),
                        r.getPlot(),
                        r.getDistance(),
                        1.0 - r.getDistance(),
                        r.getPosterUrl(),
                        r.getImdbRating(),
                        r.getImdbId(),
                        toList(r.getActors()),
                        r.getDirectors()
                ))
                .toList();

    }
}
