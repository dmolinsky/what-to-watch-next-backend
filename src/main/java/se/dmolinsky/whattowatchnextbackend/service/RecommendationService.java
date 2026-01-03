package se.dmolinsky.whattowatchnextbackend.service;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import se.dmolinsky.whattowatchnextbackend.domain.Title;
import se.dmolinsky.whattowatchnextbackend.dto.RecommendationDto;
import se.dmolinsky.whattowatchnextbackend.repository.TitleRepository;

import java.util.List;

@Service
public class RecommendationService {

    private final TitleRepository titleRepository;

    public RecommendationService(TitleRepository titleRepository) {
        this.titleRepository = titleRepository;
    }

    public List<RecommendationDto> recommendByTitle(String queryTitle, int limit) {
        Title base = titleRepository.findFirstByTitleIgnoreCase(queryTitle)
                .orElseThrow(() -> new NotFoundException("Title not found: " + queryTitle));

        return recommendById(base.getId(), limit);
    }

    @Cacheable(
            value = "recommendations",
            key = "#baseId + ':' + #limit"
    )
    public List<RecommendationDto> recommendById(Integer baseId, int limit) {
        // If the base title has no combined embedding, the query returns empty.
        var rows = titleRepository.findRecommendationsByBaseId(baseId, limit);

        if (rows.isEmpty()) {
            // could be: title missing embedding, or there are no other embeddings
            throw new NotFoundException("No combined embedding available for title id: " + baseId);
        }

        return rows.stream()
                .map(r -> new RecommendationDto(
                        r.getId(),
                        r.getTitle(),
                        r.getYear(),
                        r.getType(),
                        null, // genres mapping later
                        r.getPlot(),
                        r.getDistance(),
                        1.0 - r.getDistance()
                ))
                .toList();
    }
}
