package se.dmolinsky.whattowatchnextbackend.dto;

import java.util.List;

public record TitleDetailDto(
        Integer id,
        String title,
        Integer year,
        String type,
        List<String> genres,
        String plot,
        String directors,
        List<String> actors,
        Double imdbRating,
        String posterUrl
) {}