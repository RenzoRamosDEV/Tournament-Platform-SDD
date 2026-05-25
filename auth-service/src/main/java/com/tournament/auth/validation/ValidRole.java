package com.tournament.auth.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import java.lang.annotation.*;

@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = RoleValidator.class)
public @interface ValidRole {
    String message() default "role must be one of: admin, organizer, player";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
