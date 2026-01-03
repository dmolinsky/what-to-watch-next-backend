package se.dmolinsky.whattowatchnextbackend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import se.dmolinsky.whattowatchnextbackend.service.NotFoundException;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ResponseStatus(HttpStatus.NOT_FOUND)
    @ExceptionHandler(NotFoundException.class)
    public String handleNotFound(NotFoundException ex) {
        return ex.getMessage();
    }
}