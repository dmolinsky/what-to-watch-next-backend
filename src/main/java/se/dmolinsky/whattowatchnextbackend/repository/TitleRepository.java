package se.dmolinsky.whattowatchnextbackend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import se.dmolinsky.whattowatchnextbackend.domain.Title;

public interface TitleRepository extends JpaRepository<Title, Integer> {
}