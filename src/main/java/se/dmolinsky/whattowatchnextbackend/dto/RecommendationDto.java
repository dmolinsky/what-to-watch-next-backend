package se.dmolinsky.whattowatchnextbackend.dto;

import java.util.List;

public record RecommendationDto(
        Integer id,
        String title,
        Integer year,
        String type,
        List<String> genres,
        String plot,
        Double distance,
        Double similarity,
        String posterUrl,
        Double imdbRating,
        List<String> actors,
        String directors
) {}