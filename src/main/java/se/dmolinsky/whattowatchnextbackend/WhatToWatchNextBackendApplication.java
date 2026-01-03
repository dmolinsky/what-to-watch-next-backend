package se.dmolinsky.whattowatchnextbackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@EnableCaching
@SpringBootApplication
public class WhatToWatchNextBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(WhatToWatchNextBackendApplication.class, args);
	}

}
