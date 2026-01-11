package se.dmolinsky.whattowatchnextbackend.controller;

import org.springframework.web.bind.annotation.*;
import se.dmolinsky.whattowatchnextbackend.domain.Title;
import se.dmolinsky.whattowatchnextbackend.dto.TitleDetailDto;
import se.dmolinsky.whattowatchnextbackend.service.BadRequestException;
import se.dmolinsky.whattowatchnextbackend.service.TitleService;

import java.util.Arrays;
import java.util.List;

@RestController
@RequestMapping("/api/titles")
public class TitleController {

    private final TitleService titleService;

    public TitleController(TitleService titleService) {
        this.titleService = titleService;
    }

    private static List<String> toList(String[] arr) {
        return arr == null ? null : Arrays.asList(arr);
    }

    private static String firstOrNull(String[] arr) {
        return (arr == null || arr.length == 0) ? null : arr[0];
    }

    @GetMapping("/{id}")
    public TitleDetailDto getById(@PathVariable Integer id) {
        if (id == null || id <= 0) {
            throw new BadRequestException("id must be a positive integer");
        }

        Title t = titleService.getByIdOrThrow(id);

        return new TitleDetailDto(
                t.getId(),
                t.getTitle(),
                t.getYear(),
                t.getType(),
                toList(t.getGenres()),
                t.getPlot(),
                firstOrNull(t.getDirectors()),
                toList(t.getActors()),
                t.getImdbRating(),
                t.getPosterUrl()
        );
    }

    @GetMapping("/lookup")
    public TitleLookupResponse lookup(@RequestParam String title) {
        Title t = titleService.getByTitleOrThrow(title);
        return new TitleLookupResponse(t.getId(), t.getTitle());
    }

    public record TitleLookupResponse(Integer id, String title) {}
}
