"""Tests for authentication service.

Tests user registration, login, admin operations, and user management.
"""

import unittest
import os
import tempfile
from pathlib import Path

from src.auth.auth_service import AuthService
from src.database.repositories.user_repository import UserRepository
from src.database.db_config import set_database_path


class TestAuthService(unittest.TestCase):
    """Test cases for AuthService functionality."""
    
    def setUp(self):
        """Set up test database and service instances."""
        # Create temporary database for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        
        # Set the test database path
        set_database_path(self.test_db_path)
        
        # Initialize repository and service
        self.user_repository = UserRepository(self.test_db_path)
        self.auth_service = AuthService(self.user_repository)
    
    def tearDown(self):
        """Clean up test database."""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_user_registration(self):
        """Test user registration with valid data."""
        # Register a new user
        success, user, message = self.auth_service.register(
            username="testuser",
            password="password123",
            confirm_password="password123"
        )
        
        self.assertTrue(success, f"Registration failed: {message}")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertFalse(user.is_admin)
        self.assertIsNotNone(user.id)
    
    def test_registration_duplicate_username(self):
        """Test that duplicate usernames are rejected."""
        # Register first user
        self.auth_service.register("alice", "password123")
        
        # Try to register with same username
        success, user, message = self.auth_service.register(
            username="alice",
            password="different123"
        )
        
        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIn("already taken", message)
    
    def test_registration_validation(self):
        """Test registration validation rules."""
        # Test short username
        success, _, message = self.auth_service.register("ab", "password123")
        self.assertFalse(success)
        self.assertIn("at least 3 characters", message)
        
        # Test short password
        success, _, message = self.auth_service.register("validuser", "1234")
        self.assertFalse(success)
        self.assertIn("longer than 4 characters", message)
        
        # Test password mismatch
        success, _, message = self.auth_service.register(
            "validuser", "password123", "different123"
        )
        self.assertFalse(success)
        self.assertIn("do not match", message)
    
    def test_user_login(self):
        """Test user login after registration."""
        # Register a user
        self.auth_service.register("logintest", "mypassword123")
        
        # Test successful login
        success, user, message = self.auth_service.login("logintest", "mypassword123")
        
        self.assertTrue(success, f"Login failed: {message}")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "logintest")
        self.assertIsNotNone(user.last_login)
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register a user
        self.auth_service.register("testuser", "correctpass")
        
        # Try login with wrong password
        success, user, message = self.auth_service.login("testuser", "wrongpass")
        
        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIn("Invalid username or password", message)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent username."""
        success, user, message = self.auth_service.login("nonexistent", "anypass")
        
        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIn("Invalid username or password", message)
    
    def test_admin_login(self):
        """Test that rootusr admin account can login."""
        # Login as rootusr with default password
        success, user, message = self.auth_service.login("rootusr", "1234")
        
        self.assertTrue(success, f"Admin login failed: {message}")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "rootusr")
        self.assertTrue(user.is_admin)
    
    def test_change_password(self):
        """Test password change functionality."""
        # Register a user
        self.auth_service.register("passchange", "oldpass123")
        user = self.user_repository.find_by_username("passchange")
        
        # Change password
        success, message = self.auth_service.change_password(
            user.id, "oldpass123", "newpass123"
        )
        
        self.assertTrue(success, f"Password change failed: {message}")
        
        # Test login with new password
        success, _, _ = self.auth_service.login("passchange", "newpass123")
        self.assertTrue(success)
        
        # Test login with old password should fail
        success, _, _ = self.auth_service.login("passchange", "oldpass123")
        self.assertFalse(success)
    
    def test_reset_admin_password(self):
        """Test admin password reset functionality."""
        # Reset admin password
        success, message = self.auth_service.reset_admin_password("1234", "newadmin456")
        
        self.assertTrue(success, f"Admin password reset failed: {message}")
        
        # Test login with new password
        success, _, _ = self.auth_service.login("rootusr", "newadmin456")
        self.assertTrue(success)
        
        # Test login with old password should fail
        success, _, _ = self.auth_service.login("rootusr", "1234")
        self.assertFalse(success)
    
    def test_user_management_delete(self):
        """Test admin user deletion functionality."""
        # Get admin user
        admin = self.user_repository.find_by_username("rootusr")
        
        # Create a regular user
        self.auth_service.register("tobedeleted", "password123")
        
        # Admin deletes the user
        success, message = self.auth_service.delete_user(admin.id, "tobedeleted")
        
        self.assertTrue(success, f"User deletion failed: {message}")
        
        # Verify user is deleted
        deleted_user = self.user_repository.find_by_username("tobedeleted")
        self.assertIsNone(deleted_user)
    
    def test_non_admin_cannot_delete(self):
        """Test that non-admin users cannot delete others."""
        # Create two regular users
        self.auth_service.register("user1", "password123")
        self.auth_service.register("user2", "password123")
        
        user1 = self.user_repository.find_by_username("user1")
        
        # User1 tries to delete user2
        success, message = self.auth_service.delete_user(user1.id, "user2")
        
        self.assertFalse(success)
        self.assertIn("Admin permission required", message)
        
        # Verify user2 still exists
        user2 = self.user_repository.find_by_username("user2")
        self.assertIsNotNone(user2)
    
    def test_cannot_delete_rootusr(self):
        """Test that rootusr cannot be deleted."""
        admin = self.user_repository.find_by_username("rootusr")
        
        # Try to delete rootusr
        success, message = self.auth_service.delete_user(admin.id, "rootusr")
        
        self.assertFalse(success)
        self.assertIn("Cannot delete the root admin user", message)
        
        # Verify rootusr still exists
        rootusr = self.user_repository.find_by_username("rootusr")
        self.assertIsNotNone(rootusr)
    
    def test_admin_cannot_delete_self(self):
        """Test that admin cannot delete their own account."""
        admin = self.user_repository.find_by_username("rootusr")
        
        # Admin tries to delete themselves
        success, message = self.auth_service.delete_user(admin.id, "rootusr")
        
        self.assertFalse(success)
        # Should fail because it's trying to delete rootusr
        
    def test_is_username_taken(self):
        """Test username availability check."""
        # Check non-existent username
        self.assertFalse(self.auth_service.is_username_taken("newuser"))
        
        # Register a user
        self.auth_service.register("existinguser", "password123")
        
        # Check existing username
        self.assertTrue(self.auth_service.is_username_taken("existinguser"))
        
        # Check rootusr
        self.assertTrue(self.auth_service.is_username_taken("rootusr"))


if __name__ == "__main__":
    unittest.main()