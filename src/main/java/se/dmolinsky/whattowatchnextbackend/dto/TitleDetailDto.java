package se.dmolinsky.whattowatchnextbackend.dto;

public record TitleDetailDto(
        Integer id,
        String title,
        Integer year,
        String type
) {}