package se.dmolinsky.whattowatchnextbackend.controller;

import org.springframework.web.bind.annotation.*;
import se.dmolinsky.whattowatchnextbackend.dto.RecommendationDto;
import se.dmolinsky.whattowatchnextbackend.service.RecommendationService;

import java.util.List;

@RestController
@RequestMapping("/api/titles")
public class RecommendationController {

    private final RecommendationService recommendationService;

    public RecommendationController(RecommendationService recommendationService) {
        this.recommendationService = recommendationService;
    }

    @GetMapping("/{id}/recommendations")
    public List<RecommendationDto> recommendations(
            @PathVariable Integer id,
            @RequestParam(defaultValue = "5") int limit
    ) {
        return recommendationService.recommendById(id, limit);
    }
}
