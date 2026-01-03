package se.dmolinsky.whattowatchnextbackend.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.NoArgsConstructor;

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
}