package se.dmolinsky.whattowatchnextbackend.dto;

import java.util.List;

public record RecommendationDto(
        Integer id,
        String title,
        Integer year,
        String type,
        List<String> genres,
        String plot,
        double distance,
        double similarity
) {}