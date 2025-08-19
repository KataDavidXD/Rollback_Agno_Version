"""Authentication service for user registration and login.

Handles user registration, login, and authentication operations.
"""

from typing import Optional, Tuple
from datetime import datetime
import sqlite3

from src.auth.user import User
from src.auth.validators import validate_registration_data, validate_password
from src.database.repositories.user_repository import UserRepository


class AuthService:
    """Service for handling authentication operations.
    
    Provides methods for user registration, login, and password management.
    
    Attributes:
        user_repository: Repository for user database operations.
    
    Example:
        >>> auth = AuthService()
        >>> success, user, msg = auth.register("alice", "password123")
        >>> if success:
        ...     print(f"Registered user: {user.username}")
        >>> success, user, msg = auth.login("alice", "password123")
        >>> if success:
        ...     print(f"Logged in as: {user.username}")
    """
    
    def __init__(self, user_repository: Optional[UserRepository] = None):
        """Initialize the authentication service.
        
        Args:
            user_repository: Optional custom repository. If None, creates default.
        """
        self.user_repository = user_repository or UserRepository()
    
    def is_username_taken(self, username: str) -> bool:
        """Check if a username already exists in the database.
        
        Args:
            username: The username to check.
            
        Returns:
            True if username exists, False otherwise.
        """
        existing_user = self.user_repository.find_by_username(username)
        return existing_user is not None
    
    def register(self, username: str, password: str, 
                 confirm_password: Optional[str] = None) -> Tuple[bool, Optional[User], str]:
        """Register a new user.
        
        Args:
            username: The desired username.
            password: The password for the account.
            confirm_password: Optional password confirmation.
            
        Returns:
            Tuple of (success, user_object, message).
            
        Note:
            - Validates all input data before attempting registration
            - Checks for username uniqueness
            - Returns the created user object on success
        """
        # Validate registration data
        is_valid, error_msg = validate_registration_data(
            username, password, confirm_password
        )
        if not is_valid:
            return False, None, error_msg
        
        # Check if username already exists
        if self.is_username_taken(username):
            return False, None, f"Username '{username}' is already taken"
        
        # Create new user
        try:
            new_user = User(
                username=username,
                created_at=datetime.now()
            )
            new_user.set_password(password)
            
            # Save to database
            saved_user = self.user_repository.save(new_user)
            
            return True, saved_user, f"User '{username}' registered successfully"
            
        except sqlite3.IntegrityError:
            # Handle race condition where username was taken between check and insert
            return False, None, f"Username '{username}' is already taken"
        except Exception as e:
            return False, None, f"Registration failed: {str(e)}"
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """Authenticate a user login.
        
        Args:
            username: The username to authenticate.
            password: The password to verify.
            
        Returns:
            Tuple of (success, user_object, message).
            
        Note:
            - Updates last_login timestamp on successful login
            - Returns full user object for session management
        """
        # Find user by username
        user = self.user_repository.find_by_username(username)
        if not user:
            return False, None, "Invalid username or password"
        
        # Verify password
        if not user.verify_password(password):
            return False, None, "Invalid username or password"
        
        # Update last login time
        try:
            user.last_login = datetime.now()
            self.user_repository.save(user)
            
            return True, user, f"Successfully logged in as '{username}'"
            
        except Exception as e:
            # Still return success even if last_login update fails
            return True, user, f"Logged in (warning: could not update last login time)"
    
    def change_password(self, user_id: int, current_password: str, 
                       new_password: str) -> Tuple[bool, str]:
        """Change a user's password.
        
        Args:
            user_id: The ID of the user changing their password.
            current_password: The current password for verification.
            new_password: The new password to set.
            
        Returns:
            Tuple of (success, message).
        """
        # Find user
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not user.verify_password(current_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        # Update password
        try:
            user.set_password(new_password)
            self.user_repository.save(user)
            return True, "Password changed successfully"
            
        except Exception as e:
            return False, f"Failed to change password: {str(e)}"
    
    def reset_admin_password(self, current_password: str, 
                           new_password: str) -> Tuple[bool, str]:
        """Reset the rootusr admin password.
        
        Args:
            current_password: The current rootusr password.
            new_password: The new password to set.
            
        Returns:
            Tuple of (success, message).
            
        Note:
            Special method for resetting the rootusr password as mentioned
            in the architecture document.
        """
        # Find rootusr
        admin = self.user_repository.find_by_username("rootusr")
        if not admin:
            return False, "Admin user not found"
        
        # Verify current password
        if not admin.verify_password(current_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        # Update password
        try:
            admin.set_password(new_password)
            self.user_repository.save(admin)
            return True, "Admin password reset successfully"
            
        except Exception as e:
            return False, f"Failed to reset admin password: {str(e)}"
    
    def delete_user(self, admin_user_id: int, target_username: str) -> Tuple[bool, str]:
        """Delete a user (admin only operation).
        
        Args:
            admin_user_id: The ID of the admin user performing the deletion.
            target_username: The username of the user to delete.
            
        Returns:
            Tuple of (success, message).
            
        Note:
            Only rootusr or admin users can delete other users.
            Admin users cannot delete themselves or other admins.
        """
        # Verify admin permissions
        admin = self.user_repository.find_by_id(admin_user_id)
        if not admin or not admin.is_admin:
            return False, "Admin permission required"
        
        # Find target user
        target_user = self.user_repository.find_by_username(target_username)
        if not target_user:
            return False, f"User '{target_username}' not found"
        
        # Prevent deleting rootusr
        if target_username == "rootusr":
            return False, "Cannot delete the root admin user"
        
        # Prevent admin from deleting themselves
        if target_user.id == admin_user_id:
            return False, "Cannot delete your own account"
        
        # Delete the user
        try:
            success = self.user_repository.delete(target_user.id)
            if success:
                return True, f"User '{target_username}' deleted successfully"
            else:
                return False, f"Failed to delete user '{target_username}'"
                
        except Exception as e:
            return False, f"Failed to delete user: {str(e)}"