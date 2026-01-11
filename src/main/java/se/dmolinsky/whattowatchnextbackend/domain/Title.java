package se.dmolinsky.whattowatchnextbackend.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "titles")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Title {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Integer id;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "year")
    private Integer year;

    @Column(name = "type", nullable = false)
    private String type;

    @Column(name = "poster_url")
    private String posterUrl;

    @Column(name = "plot", columnDefinition = "text")
    private String plot;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "directors", columnDefinition = "text[]")
    private String[] directors;

    @Column(name = "imdb_rating")
    private Double imdbRating;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "genres", columnDefinition = "text[]")
    private String[] genres;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "actors", columnDefinition = "text[]")
    private String[] actors;

    public Integer getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public Integer getYear() {
        return year;
    }

    public String getType() {
        return type;
    }

    public String getPosterUrl() {
        return posterUrl;
    }

    public String getPlot() {
        return plot;
    }

    public String[] getDirectors() {
        return directors;
    }

    public Double getImdbRating() {
        return imdbRating;
    }

    public String[] getGenres() {
        return genres;
    }

    public String[] getActors() {
        return actors;
    }
}
