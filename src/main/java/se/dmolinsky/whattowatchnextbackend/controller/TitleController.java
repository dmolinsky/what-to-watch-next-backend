package se.dmolinsky.whattowatchnextbackend.controller;

import org.springframework.web.bind.annotation.*;
import se.dmolinsky.whattowatchnextbackend.domain.Title;
import se.dmolinsky.whattowatchnextbackend.dto.TitleDetailDto;
import se.dmolinsky.whattowatchnextbackend.service.TitleService;

@RestController
@RequestMapping("/api/titles")
public class TitleController {

    private final TitleService titleService;

    public TitleController(TitleService titleService) {
        this.titleService = titleService;
    }

    @GetMapping("/{id}")
    public TitleDetailDto getById(@PathVariable Integer id) {
        Title t = titleService.getByIdOrThrow(id);
        return new TitleDetailDto(t.getId(), t.getTitle(), t.getYear(), t.getType());
    }
}