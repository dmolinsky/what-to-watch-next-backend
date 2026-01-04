package se.dmolinsky.whattowatchnextbackend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import se.dmolinsky.whattowatchnextbackend.domain.Title;

import java.util.List;
import java.util.Optional;

public interface TitleRepository extends JpaRepository<Title, Integer> {

    Optional<Title> findFirstByTitleIgnoreCase(String title);

    interface RecommendationRow {
        Integer getId();
        String getTitle();
        Integer getYear();
        String getType();
        Object getGenres(); // we'll map later (text[])
        String getPlot();
        Double getDistance();
    }

    @Query(
            value = """
            SELECT
                t.id         AS id,
                t.title      AS title,
                t.year       AS year,
                t.type       AS type,
                t.genres     AS genres,
                t.plot       AS plot,
                (e.combined_embedding <=> (
                    SELECT e2.combined_embedding
                    FROM embeddings e2
                    WHERE e2.title_id = :baseId
                )) AS distance
            FROM embeddings e
            JOIN titles t ON t.id = e.title_id
            WHERE t.id <> :baseId
              AND (SELECT e2.combined_embedding FROM embeddings e2 WHERE e2.title_id = :baseId) IS NOT NULL
              AND e.combined_embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT :limit
            """,
            nativeQuery = true
    )
    List<RecommendationRow> findRecommendationsByBaseId(
            @Param("baseId") Integer baseId,
            @Param("limit") int limit
    );

    Optional<Title> findFirstByTitleContainingIgnoreCase(String title);
}