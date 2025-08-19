"""Validation rules for authentication.

Provides reusable validation functions for user registration and authentication.
"""

import re
from typing import Tuple


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format and requirements.
    
    Args:
        username: The username to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
        
    Rules:
        - Must be between 3 and 30 characters
        - Can only contain letters, numbers, and underscores
        - Must start with a letter
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return False, "Username cannot exceed 30 characters"
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username must start with a letter and contain only letters, numbers, and underscores"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength and requirements.
    
    Args:
        password: The password to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
        
    Rules:
        - Must be more than 4 characters
        - Cannot contain spaces at the beginning or end
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) <= 4:
        return False, "Password must be longer than 4 characters"
    
    if password != password.strip():
        return False, "Password cannot start or end with spaces"
    
    return True, ""


def validate_password_match(password: str, confirm_password: str) -> Tuple[bool, str]:
    """Validate that two passwords match.
    
    Args:
        password: The original password.
        confirm_password: The confirmation password.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if password != confirm_password:
        return False, "Passwords do not match"
    
    return True, ""


def validate_admin_permission(requesting_user_is_admin: bool) -> Tuple[bool, str]:
    """Validate that a user has admin permissions for certain operations.
    
    Args:
        requesting_user_is_admin: Whether the requesting user is an admin.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not requesting_user_is_admin:
        return False, "Admin permission required for this operation"
    
    return True, ""


def validate_registration_data(username: str, password: str, confirm_password: str = None) -> Tuple[bool, str]:
    """Validate all registration data.
    
    Args:
        username: The username to register.
        password: The password for the account.
        confirm_password: Optional password confirmation.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return False, error_msg
    
    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return False, error_msg
    
    # Validate password match if confirmation provided
    if confirm_password is not None:
        is_valid, error_msg = validate_password_match(password, confirm_password)
        if not is_valid:
            return False, error_msg
    
    return True, ""