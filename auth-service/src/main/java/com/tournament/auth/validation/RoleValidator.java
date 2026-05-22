package com.tournament.auth.validation;

import com.tournament.auth.domain.User;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

public class RoleValidator implements ConstraintValidator<ValidRole, String> {

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) return false;
        return User.VALID_ROLES.contains(value.toLowerCase());
    }
}
