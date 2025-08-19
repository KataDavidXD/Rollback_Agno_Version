"""Tests for external session repository.

Tests CRUD operations, user ownership, and internal session tracking.
"""

import unittest
import os
import tempfile
from datetime import datetime

from src.sessions.external_session import ExternalSession
from src.database.repositories.external_session_repository import ExternalSessionRepository
from src.database.repositories.user_repository import UserRepository
from src.auth.user import User
from src.database.db_config import set_database_path


class TestExternalSessionRepository(unittest.TestCase):
    """Test cases for ExternalSessionRepository functionality."""
    
    def setUp(self):
        """Set up test database and repository instances."""
        # Create temporary database for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        
        # Set the test database path
        set_database_path(self.test_db_path)
        
        # Initialize repositories
        self.user_repo = UserRepository(self.test_db_path)
        self.session_repo = ExternalSessionRepository(self.test_db_path)
        
        # Create test users
        self.user1 = User(username="testuser1", created_at=datetime.now())
        self.user1.set_password("password123")
        self.user1 = self.user_repo.save(self.user1)
        
        self.user2 = User(username="testuser2", created_at=datetime.now())
        self.user2.set_password("password456")
        self.user2 = self.user_repo.save(self.user2)
    
    def tearDown(self):
        """Clean up test database."""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_create_session(self):
        """Test creating a new external session."""
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="Test Session",
            created_at=datetime.now()
        )
        
        saved_session = self.session_repo.create(session)
        
        self.assertIsNotNone(saved_session.id)
        self.assertEqual(saved_session.user_id, self.user1.id)
        self.assertEqual(saved_session.session_name, "Test Session")
        self.assertTrue(saved_session.is_active)
        self.assertEqual(saved_session.internal_session_ids, [])
        self.assertIsNone(saved_session.current_internal_session_id)
    
    def test_create_session_with_internal_sessions(self):
        """Test creating a session with internal Agno sessions."""
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="Session with Internals"
        )
        session.add_internal_session("agno_123")
        session.add_internal_session("agno_456")
        
        saved_session = self.session_repo.create(session)
        
        self.assertEqual(len(saved_session.internal_session_ids), 2)
        self.assertIn("agno_123", saved_session.internal_session_ids)
        self.assertIn("agno_456", saved_session.internal_session_ids)
        self.assertEqual(saved_session.current_internal_session_id, "agno_456")
    
    def test_get_by_id(self):
        """Test retrieving a session by ID."""
        # Create a session
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="Retrieval Test"
        )
        session.add_internal_session("agno_test")
        created = self.session_repo.create(session)
        
        # Retrieve it
        retrieved = self.session_repo.get_by_id(created.id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, created.id)
        self.assertEqual(retrieved.session_name, "Retrieval Test")
        self.assertEqual(retrieved.user_id, self.user1.id)
        self.assertIn("agno_test", retrieved.internal_session_ids)
    
    def test_get_nonexistent_session(self):
        """Test retrieving a non-existent session returns None."""
        session = self.session_repo.get_by_id(99999)
        self.assertIsNone(session)
    
    def test_update_session(self):
        """Test updating an existing session."""
        # Create a session
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="Original Name"
        )
        created = self.session_repo.create(session)
        
        # Update it
        created.session_name = "Updated Name"
        created.add_internal_session("agno_new")
        success = self.session_repo.update(created)
        
        self.assertTrue(success)
        
        # Verify update
        updated = self.session_repo.get_by_id(created.id)
        self.assertEqual(updated.session_name, "Updated Name")
        self.assertIn("agno_new", updated.internal_session_ids)
        self.assertIsNotNone(updated.updated_at)
    
    def test_update_nonexistent_session(self):
        """Test updating a session without ID returns False."""
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="No ID Session"
        )
        success = self.session_repo.update(session)
        self.assertFalse(success)
    
    def test_delete_session(self):
        """Test permanently deleting a session."""
        # Create a session
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="To Delete"
        )
        created = self.session_repo.create(session)
        
        # Delete it
        success = self.session_repo.delete(created.id)
        self.assertTrue(success)
        
        # Verify deletion
        deleted = self.session_repo.get_by_id(created.id)
        self.assertIsNone(deleted)
    
    def test_deactivate_session(self):
        """Test soft deleting (deactivating) a session."""
        # Create a session
        session = ExternalSession(
            user_id=self.user1.id,
            session_name="To Deactivate"
        )
        created = self.session_repo.create(session)
        
        # Deactivate it
        success = self.session_repo.deactivate(created.id)
        self.assertTrue(success)
        
        # Verify deactivation
        deactivated = self.session_repo.get_by_id(created.id)
        self.assertIsNotNone(deactivated)
        self.assertFalse(deactivated.is_active)
    
    def test_get_user_sessions(self):
        """Test retrieving all sessions for a user."""
        # Create sessions for user1
        session1 = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Session 1")
        )
        session2 = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Session 2")
        )
        
        # Create session for user2
        self.session_repo.create(
            ExternalSession(user_id=self.user2.id, session_name="Other User Session")
        )
        
        # Get user1's sessions
        user1_sessions = self.session_repo.get_user_sessions(self.user1.id)
        
        self.assertEqual(len(user1_sessions), 2)
        session_names = [s.session_name for s in user1_sessions]
        self.assertIn("Session 1", session_names)
        self.assertIn("Session 2", session_names)
    
    def test_get_active_sessions_only(self):
        """Test retrieving only active sessions."""
        # Create active session
        active = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Active")
        )
        
        # Create and deactivate another session
        inactive = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Inactive")
        )
        self.session_repo.deactivate(inactive.id)
        
        # Get only active sessions
        active_sessions = self.session_repo.get_user_sessions(
            self.user1.id, active_only=True
        )
        
        self.assertEqual(len(active_sessions), 1)
        self.assertEqual(active_sessions[0].session_name, "Active")
    
    def test_check_ownership(self):
        """Test verifying session ownership."""
        # Create session for user1
        session = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="User1 Session")
        )
        
        # Check ownership
        owns = self.session_repo.check_ownership(session.id, self.user1.id)
        self.assertTrue(owns)
        
        # Check non-ownership
        not_owns = self.session_repo.check_ownership(session.id, self.user2.id)
        self.assertFalse(not_owns)
    
    def test_count_user_sessions(self):
        """Test counting user sessions."""
        # Initially no sessions
        count = self.session_repo.count_user_sessions(self.user1.id)
        self.assertEqual(count, 0)
        
        # Create sessions
        self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Session 1")
        )
        self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="Session 2")
        )
        
        # Count all sessions
        count = self.session_repo.count_user_sessions(self.user1.id)
        self.assertEqual(count, 2)
        
        # Count active only (all are active)
        active_count = self.session_repo.count_user_sessions(
            self.user1.id, active_only=True
        )
        self.assertEqual(active_count, 2)
    
    def test_add_internal_session(self):
        """Test adding internal Agno sessions."""
        # Create external session
        session = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="External")
        )
        
        # Add internal sessions
        success1 = self.session_repo.add_internal_session(session.id, "agno_001")
        success2 = self.session_repo.add_internal_session(session.id, "agno_002")
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # Verify internal sessions were added
        updated = self.session_repo.get_by_id(session.id)
        self.assertEqual(len(updated.internal_session_ids), 2)
        self.assertIn("agno_001", updated.internal_session_ids)
        self.assertIn("agno_002", updated.internal_session_ids)
        self.assertEqual(updated.current_internal_session_id, "agno_002")
    
    def test_set_current_internal_session(self):
        """Test setting the current internal session."""
        # Create session with internal sessions
        session = ExternalSession(user_id=self.user1.id, session_name="Multi Internal")
        session.add_internal_session("agno_a")
        session.add_internal_session("agno_b")
        created = self.session_repo.create(session)
        
        # Current should be the last added
        self.assertEqual(created.current_internal_session_id, "agno_b")
        
        # Change current session
        success = self.session_repo.set_current_internal_session(created.id, "agno_a")
        self.assertTrue(success)
        
        # Verify change
        updated = self.session_repo.get_by_id(created.id)
        self.assertEqual(updated.current_internal_session_id, "agno_a")
        
        # Try setting non-existent internal session
        success = self.session_repo.set_current_internal_session(created.id, "agno_invalid")
        self.assertFalse(success)
    
    def test_get_by_internal_session(self):
        """Test finding external session by internal Agno session ID."""
        # Create sessions with internal sessions
        session1 = ExternalSession(user_id=self.user1.id, session_name="Session 1")
        session1.add_internal_session("agno_unique_1")
        self.session_repo.create(session1)
        
        session2 = ExternalSession(user_id=self.user2.id, session_name="Session 2")
        session2.add_internal_session("agno_unique_2")
        self.session_repo.create(session2)
        
        # Find by internal session
        found = self.session_repo.get_by_internal_session("agno_unique_1")
        self.assertIsNotNone(found)
        self.assertEqual(found.session_name, "Session 1")
        self.assertEqual(found.user_id, self.user1.id)
        
        # Try non-existent internal session
        not_found = self.session_repo.get_by_internal_session("agno_nonexistent")
        self.assertIsNone(not_found)
    
    def test_session_isolation_between_users(self):
        """Test that users can only access their own sessions."""
        # Create session for user1
        user1_session = self.session_repo.create(
            ExternalSession(user_id=self.user1.id, session_name="User1 Private")
        )
        
        # Create session for user2
        user2_session = self.session_repo.create(
            ExternalSession(user_id=self.user2.id, session_name="User2 Private")
        )
        
        # Get sessions for each user
        user1_sessions = self.session_repo.get_user_sessions(self.user1.id)
        user2_sessions = self.session_repo.get_user_sessions(self.user2.id)
        
        # Verify isolation
        self.assertEqual(len(user1_sessions), 1)
        self.assertEqual(user1_sessions[0].session_name, "User1 Private")
        
        self.assertEqual(len(user2_sessions), 1)
        self.assertEqual(user2_sessions[0].session_name, "User2 Private")
        
        # Verify ownership checks
        self.assertTrue(self.session_repo.check_ownership(user1_session.id, self.user1.id))
        self.assertFalse(self.session_repo.check_ownership(user1_session.id, self.user2.id))
        
        self.assertTrue(self.session_repo.check_ownership(user2_session.id, self.user2.id))
        self.assertFalse(self.session_repo.check_ownership(user2_session.id, self.user1.id))


if __name__ == "__main__":
    unittest.main()