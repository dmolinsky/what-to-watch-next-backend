package se.dmolinsky.whattowatchnextbackend.service;

import org.springframework.stereotype.Service;
import se.dmolinsky.whattowatchnextbackend.domain.Title;
import se.dmolinsky.whattowatchnextbackend.repository.TitleRepository;

import java.util.Optional;


@Service
public class TitleService {
    private final TitleRepository titleRepository;

    public TitleService(TitleRepository titleRepository) {
        this.titleRepository = titleRepository;
    }

    public Title getByIdOrThrow(Integer id) {
        Optional<Title> optional = titleRepository.findById(id);

        if (optional.isEmpty()) {
            throw new NotFoundException("Title not found: " + id);
        }

        return optional.get();
    }

}