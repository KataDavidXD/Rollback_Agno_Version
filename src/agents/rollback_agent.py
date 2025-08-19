"""Custom Agno Agent with rollback capabilities.

Extends Agno's Agent to add automatic checkpoint creation and database persistence.
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import uuid

from agno.agent import Agent
from agno.storage.sqlite import SqliteStorage

from src.sessions.internal_session import InternalSession
from src.checkpoints.checkpoint import Checkpoint
from src.database.repositories.external_session_repository import ExternalSessionRepository


class RollbackAgent(Agent):
    """Agent with checkpoint and rollback capabilities.
    
    Extends Agno's Agent to automatically save session state and conversation
    history to the database after each run. Supports automatic checkpoint
    creation after tool calls.
    
    Attributes:
        external_session_id: ID of the external session this agent belongs to.
        internal_session: The current internal session being used.
        auto_checkpoint: Whether to automatically create checkpoints after tool calls.
        internal_session_repo: Repository for internal session operations.
        checkpoint_repo: Repository for checkpoint operations.
        external_session_repo: Repository for external session operations.
    """
    
    def __init__(
        self,
        external_session_id: int,
        model,
        auto_checkpoint: bool = True,
        internal_session_repo=None,
        checkpoint_repo=None,
        skip_session_creation: bool = False,
        **kwargs
    ):
        """Initialize the RollbackAgent.
        
        Args:
            external_session_id: ID of the external session.
            model: The Agno model to use (e.g., OpenAIChat).
            auto_checkpoint: Whether to auto-checkpoint after tool calls.
            internal_session_repo: Optional internal session repository.
            checkpoint_repo: Optional checkpoint repository.
            skip_session_creation: Skip creating a new internal session (for resume/rollback).
            **kwargs: Additional arguments passed to Agno Agent.
        """
        # Generate a unique Agno session ID
        agno_session_id = f"agno_{uuid.uuid4().hex[:12]}"
        
        # Set up storage if not provided
        if 'storage' not in kwargs:
            kwargs['storage'] = SqliteStorage(
                table_name=f"agno_session_{agno_session_id}",
                db_file="data/agno_sessions.db",
                auto_upgrade_schema=True
            )
        
        # Track tool usage for automatic checkpointing
        self._tool_was_called = False
        self._last_tool_called = None
        
        # Create a tool hook to detect tool calls
        def checkpoint_hook(function_name: str, function_call, arguments: Dict[str, Any]):
            """Hook that tracks tool calls for automatic checkpointing."""
            self._tool_was_called = True
            self._last_tool_called = function_name
            # Execute the actual tool
            return function_call(**arguments)
        
        # Add our hook to any existing hooks
        if 'tool_hooks' not in kwargs:
            kwargs['tool_hooks'] = [checkpoint_hook]
        else:
            if isinstance(kwargs['tool_hooks'], list):
                kwargs['tool_hooks'].append(checkpoint_hook)
        
        # Add checkpoint management tools to the agent
        # These methods serve as both tools for the agent and regular methods
        checkpoint_tools = [
            self.create_checkpoint_tool, 
            self.list_checkpoints_tool,
            self.rollback_to_checkpoint_tool,
            self.delete_checkpoint_tool,
            self.get_checkpoint_info_tool,
            self.cleanup_auto_checkpoints_tool
        ]
        
        if 'tools' not in kwargs:
            kwargs['tools'] = checkpoint_tools
        else:
            # Add checkpoint tools to existing tools
            if isinstance(kwargs['tools'], list):
                kwargs['tools'].extend(checkpoint_tools)
        
        # Initialize the parent Agent with the session_id
        super().__init__(model=model, session_id=agno_session_id, **kwargs)
        
        self.external_session_id = external_session_id
        self.agno_session_id = agno_session_id
        self.auto_checkpoint = auto_checkpoint
        
        # Initialize repositories (will be injected in production)
        self.internal_session_repo = internal_session_repo
        self.checkpoint_repo = checkpoint_repo
        self.external_session_repo = ExternalSessionRepository()
        
        # Flags for restored state
        self._restored_from_checkpoint = False
        self._restored_history = []
        
        # Create internal session only if not skipping (for resume/rollback)
        if not skip_session_creation:
            self.internal_session = self._create_internal_session()
            # Update external session with this internal session
            self._register_with_external_session()
        else:
            # Will be set by the caller
            self.internal_session = None
    
    def _create_internal_session(self) -> InternalSession:
        """Create a new internal session for this agent.
        
        Returns:
            The created InternalSession object.
        """
        internal_session = InternalSession(
            external_session_id=self.external_session_id,
            agno_session_id=self.agno_session_id,
            session_state=self.session_state or {},
            created_at=datetime.now(),
            is_current=True
        )
        
        # Save to database if repository is available
        if self.internal_session_repo:
            internal_session = self.internal_session_repo.create(internal_session)
        
        return internal_session
    
    def _register_with_external_session(self):
        """Register this internal session with the external session."""
        if self.external_session_repo:
            self.external_session_repo.add_internal_session(
                self.external_session_id,
                self.agno_session_id
            )
    
    def run(self, message: str, **kwargs) -> Any:
        """Run the agent and save state after completion.
        
        Overrides the parent run method to add:
        1. Automatic state and history persistence
        2. Automatic checkpoint creation after tool calls (except checkpoint tools)
        
        Args:
            message: The user message to process.
            **kwargs: Additional arguments for the run.
            
        Returns:
            The agent's response.
        """
        # Store the message in conversation history
        self.internal_session.add_message("user", message)
        
        # If this is the first run after restoration, inject the history
        if self._restored_from_checkpoint and self._restored_history:
            # Convert restored history to the format expected by Agno
            if 'messages' not in kwargs:
                kwargs['messages'] = []
            
            # Add the restored conversation history as context
            for msg in self._restored_history:
                kwargs['messages'].append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Clear the flag after injection
            self._restored_from_checkpoint = False
        
        # Reset tool tracking before running
        self._tool_was_called = False
        self._last_tool_called = None
        
        # Call parent run method with potentially injected messages
        response = super().run(message, **kwargs)
        
        # Extract response content
        response_content = self._extract_response_content(response)
        
        # Store the response in conversation history
        self.internal_session.add_message("assistant", response_content)
        
        # Update session state from agent
        self.internal_session.update_state(self.session_state)
        
        # Check if tool was called using our hook and create checkpoint if needed
        # Skip auto-checkpoint if checkpoint management tools were used
        if self.auto_checkpoint and self._tool_was_called:
            if not self._is_checkpoint_tool(self._last_tool_called):
                self._create_auto_checkpoint(f"After {self._last_tool_called}")
        
        # Save the updated internal session to database
        self._save_internal_session()
        
        return response
    
    def _extract_response_content(self, response) -> str:
        """Extract the content from the agent response.
        
        Args:
            response: The response from the agent.
            
        Returns:
            The extracted content as a string.
        """
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, dict) and 'content' in response:
            return response['content']
        elif isinstance(response, str):
            return response
        else:
            return str(response)
    
    def _has_tool_calls(self, response) -> bool:
        """Check if the response contains tool calls.
        
        Args:
            response: The response from the agent.
            
        Returns:
            True if tool calls were made, False otherwise.
        """
        if hasattr(response, 'tool_calls'):
            return bool(response.tool_calls)
        elif isinstance(response, dict):
            return bool(response.get('tool_calls'))
        return False
    
    def _is_checkpoint_tool(self, tool_name: Optional[str]) -> bool:
        """Check if a tool is a checkpoint management tool.
        
        Args:
            tool_name: Name of the tool that was called.
            
        Returns:
            True if it's a checkpoint tool, False otherwise.
        """
        if not tool_name:
            return False
            
        checkpoint_tool_names = {
            'create_checkpoint_tool',
            'list_checkpoints_tool', 
            'rollback_to_checkpoint_tool',
            'delete_checkpoint_tool',
            'get_checkpoint_info_tool',
            'cleanup_auto_checkpoints_tool'
        }
        
        return tool_name in checkpoint_tool_names
    
    def _used_checkpoint_tools(self, response) -> bool:
        """Check if checkpoint management tools were used.
        
        DEPRECATED: This method is kept for compatibility but is no longer used.
        We now use tool hooks to detect tool calls instead.
        
        Args:
            response: The response from the agent.
            
        Returns:
            True if checkpoint tools were used, False otherwise.
        """
        checkpoint_tool_names = {
            'create_checkpoint_tool',
            'list_checkpoints_tool', 
            'rollback_to_checkpoint_tool',
            'delete_checkpoint_tool',
            'get_checkpoint_info_tool',
            'cleanup_auto_checkpoints_tool'
        }
        
        if hasattr(response, 'tool_calls'):
            for tool_call in response.tool_calls:
                if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                    if tool_call.function.name in checkpoint_tool_names:
                        return True
        elif isinstance(response, dict) and 'tool_calls' in response:
            for tool_call in response['tool_calls']:
                if isinstance(tool_call, dict) and tool_call.get('function', {}).get('name') in checkpoint_tool_names:
                    return True
        
        return False
    
    def _create_auto_checkpoint(self, name: str):
        """Create an automatic checkpoint.
        
        Args:
            name: Name for the checkpoint.
        """
        if self.checkpoint_repo and self.internal_session.id:
            checkpoint = Checkpoint.from_internal_session(
                self.internal_session,
                checkpoint_name=name,
                is_auto=True
            )
            self.checkpoint_repo.create(checkpoint)
            self.internal_session.checkpoint_count += 1
    
    # Checkpoint management tools for the agent
    def create_checkpoint_tool(self, name: Optional[str] = None) -> str:
        """Create a manual checkpoint of the current conversation state.
        
        Args:
            name: Optional name for the checkpoint. If not provided, a timestamp will be used.
            
        Returns:
            A message confirming checkpoint creation.
        """
        if not name:
            name = f"Checkpoint at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if self.checkpoint_repo and self.internal_session.id:
            checkpoint = Checkpoint.from_internal_session(
                self.internal_session,
                checkpoint_name=name,
                is_auto=False
            )
            saved_checkpoint = self.checkpoint_repo.create(checkpoint)
            self.internal_session.checkpoint_count += 1
            self._save_internal_session()
            
            if saved_checkpoint:
                return f"✓ Checkpoint '{name}' created successfully (ID: {saved_checkpoint.id})"
        
        return "Failed to create checkpoint. Repository or session not available."
    
    # Alias for backward compatibility and programmatic use
    create_checkpoint = create_checkpoint_tool
    
    def list_checkpoints_tool(self) -> str:
        """List all available checkpoints for the current session.
        
        Returns:
            A formatted list of available checkpoints.
        """
        if not self.checkpoint_repo or not self.internal_session.id:
            return "No active session or checkpoint functionality unavailable."
        
        checkpoints = self.checkpoint_repo.get_by_internal_session(
            self.internal_session.id,
            auto_only=False
        )
        
        if not checkpoints:
            return "No checkpoints found for the current session."
        
        result = "Available checkpoints:\n"
        for cp in checkpoints:
            checkpoint_type = "auto" if cp.is_auto else "manual"
            created = cp.created_at.strftime('%Y-%m-%d %H:%M:%S') if cp.created_at else "unknown"
            name = cp.checkpoint_name or "Unnamed"
            result += f"\n• ID: {cp.id} | {name} | Type: {checkpoint_type} | Created: {created}"
        
        return result
    
    def rollback_to_checkpoint_tool(self, checkpoint_id_or_name) -> str:
        """Request rollback to a specific checkpoint by ID or name.
        
        Note: This marks a rollback request. The actual rollback needs to be 
        handled by the system managing the agent.
        
        Args:
            checkpoint_id_or_name: The ID (integer) or name (string) of the checkpoint to restore.
            
        Returns:
            A message indicating the rollback request status.
        """
        if not self.checkpoint_repo:
            return "Checkpoint functionality is not available."
        
        checkpoint = None
        
        # Try to parse as integer ID first
        try:
            checkpoint_id = int(checkpoint_id_or_name)
            checkpoint = self.checkpoint_repo.get_by_id(checkpoint_id)
        except (ValueError, TypeError):
            # Not an integer, try to find by name
            if self.internal_session and self.internal_session.id:
                all_checkpoints = self.checkpoint_repo.get_by_internal_session(
                    self.internal_session.id
                )
                # Find checkpoint by name (case-insensitive)
                checkpoint_name_lower = str(checkpoint_id_or_name).lower()
                for cp in all_checkpoints:
                    if cp.checkpoint_name and cp.checkpoint_name.lower() == checkpoint_name_lower:
                        checkpoint = cp
                        break
        
        if not checkpoint:
            return f"Checkpoint '{checkpoint_id_or_name}' not found. Use 'list checkpoints' to see available checkpoints."
        
        # Mark rollback request in session state
        self.session_state['rollback_requested'] = True
        self.session_state['rollback_checkpoint_id'] = checkpoint.id
        
        return (f"Rollback to checkpoint {checkpoint.id} ('{checkpoint.checkpoint_name}') requested. "
                f"The system will create a new session with the state from this checkpoint.")
    
    def delete_checkpoint_tool(self, checkpoint_id: int) -> str:
        """Delete a specific checkpoint.
        
        Args:
            checkpoint_id: The ID of the checkpoint to delete.
            
        Returns:
            A message confirming deletion.
        """
        if not self.checkpoint_repo:
            return "Checkpoint functionality is not available."
        
        checkpoint = self.checkpoint_repo.get_by_id(checkpoint_id)
        if not checkpoint:
            return f"Checkpoint with ID {checkpoint_id} not found."
        
        if checkpoint.internal_session_id != self.internal_session.id:
            return "You can only delete checkpoints from the current session."
        
        success = self.checkpoint_repo.delete(checkpoint_id)
        
        if success:
            return f"✓ Checkpoint {checkpoint_id} deleted successfully."
        else:
            return f"Failed to delete checkpoint {checkpoint_id}."
    
    def get_checkpoint_info_tool(self, checkpoint_id: int) -> str:
        """Get detailed information about a specific checkpoint.
        
        Args:
            checkpoint_id: The ID of the checkpoint to inspect.
            
        Returns:
            Detailed information about the checkpoint.
        """
        if not self.checkpoint_repo:
            return "Checkpoint functionality is not available."
        
        checkpoint = self.checkpoint_repo.get_by_id(checkpoint_id)
        if not checkpoint:
            return f"Checkpoint with ID {checkpoint_id} not found."
        
        checkpoint_type = "Automatic" if checkpoint.is_auto else "Manual"
        created = checkpoint.created_at.strftime('%Y-%m-%d %H:%M:%S') if checkpoint.created_at else "unknown"
        
        info = f"Checkpoint Details:\n"
        info += f"• ID: {checkpoint.id}\n"
        info += f"• Name: {checkpoint.checkpoint_name or 'Unnamed'}\n"
        info += f"• Type: {checkpoint_type}\n"
        info += f"• Created: {created}\n"
        info += f"• Conversation Length: {len(checkpoint.conversation_history)} messages"
        
        return info
    
    def cleanup_auto_checkpoints_tool(self, keep_latest: int = 5) -> str:
        """Clean up old automatic checkpoints, keeping only the most recent ones.
        
        Args:
            keep_latest: Number of latest automatic checkpoints to keep (default: 5).
            
        Returns:
            A message indicating how many checkpoints were deleted.
        """
        if not self.checkpoint_repo or not self.internal_session.id:
            return "No active session or checkpoint functionality unavailable."
        
        deleted_count = self.checkpoint_repo.delete_auto_checkpoints(
            self.internal_session.id,
            keep_latest=keep_latest
        )
        
        if deleted_count > 0:
            return f"✓ Cleaned up {deleted_count} old automatic checkpoints. Kept the latest {keep_latest}."
        else:
            return "No automatic checkpoints to clean up."
    
    def _save_internal_session(self):
        """Save the current internal session to the database."""
        if self.internal_session_repo and self.internal_session.id:
            self.internal_session_repo.update(self.internal_session)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history for this session.
        
        Returns:
            List of conversation messages.
        """
        return self.internal_session.conversation_history
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get the current session state.
        
        Returns:
            The session state dictionary.
        """
        return self.internal_session.session_state
    
    def get_messages_for_session(self, **kwargs):
        """Override to inject restored conversation history when applicable.
        
        This method is called by Agno when add_history_to_messages=True.
        When we restore from a checkpoint, we need to provide the conversation
        history from before the rollback so the agent has context.
        
        Returns:
            List of messages including restored history if applicable.
        """
        # Get the normal messages from Agno's storage
        messages = super().get_messages_for_session(**kwargs)
        
        # If we were restored from a checkpoint and this is the first run after restoration
        if self._restored_from_checkpoint and self._restored_history:
            # Convert our internal history format to Agno's message format
            # We need to match whatever format Agno expects
            restored_messages = []
            
            for msg in self._restored_history:
                # Create message in the same format as Agno's messages
                # Check what format the existing messages have
                if messages and hasattr(messages[0], '__class__'):
                    # Use the same class as existing messages
                    MessageClass = messages[0].__class__
                    message = MessageClass(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    )
                else:
                    # Fall back to dict format
                    message = {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                restored_messages.append(message)
            
            # Combine restored history with any new messages
            # Put restored history first, then any new messages
            combined_messages = restored_messages + messages
            
            # Note: We don't clear the flag here since it's already cleared in run()
            # This method might not be called in all scenarios
            
            return combined_messages
        
        return messages
    
    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_id: int,
        external_session_id: int,
        model,
        checkpoint_repo,
        internal_session_repo,
        **kwargs
    ) -> "RollbackAgent":
        """Create a new agent from a checkpoint (rollback).
        
        This creates a new internal session with the state from the checkpoint,
        effectively rolling back to that point.
        
        Args:
            checkpoint_id: ID of the checkpoint to restore from.
            external_session_id: ID of the external session.
            model: The Agno model to use.
            checkpoint_repo: Repository for checkpoint operations.
            internal_session_repo: Repository for internal session operations.
            **kwargs: Additional arguments for the agent.
            
        Returns:
            A new RollbackAgent with the checkpoint's state.
        """
        # Load the checkpoint
        checkpoint = checkpoint_repo.get_by_id(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        # Pass the checkpoint's session_state to the agent constructor
        # This ensures the Agno agent starts with the correct state
        if 'session_state' not in kwargs:
            kwargs['session_state'] = checkpoint.session_state.copy()
        
        # Create new agent but DON'T create a session yet
        agent = cls(
            external_session_id=external_session_id,
            model=model,
            internal_session_repo=internal_session_repo,
            checkpoint_repo=checkpoint_repo,
            skip_session_creation=True,  # We'll create the session manually
            **kwargs
        )
        
        # Now create the internal session with the checkpoint data
        agent.internal_session = agent._create_internal_session()
        agent._register_with_external_session()
        
        # Restore state and history from checkpoint
        agent.internal_session.session_state = checkpoint.session_state.copy()
        agent.internal_session.conversation_history = checkpoint.conversation_history.copy()
        
        # CRITICAL FIX: Store the restored history so it can be used in the run method
        # This flag tells our agent that we're in a restored state
        agent._restored_from_checkpoint = True
        agent._restored_history = checkpoint.conversation_history.copy()
        
        # CRITICAL FIX 2: Copy all checkpoints up to and including the restored checkpoint
        # to the new internal session for full snapshot rollback capability
        if checkpoint_repo and agent.internal_session.id:
            # Get all checkpoints from the original internal session
            original_checkpoints = checkpoint_repo.get_by_internal_session(
                checkpoint.internal_session_id,
                auto_only=False
            )
            
            # Copy checkpoints created before or at the rollback point
            for cp in original_checkpoints:
                # Only copy checkpoints created before or at the same time as our target checkpoint
                if cp.created_at and checkpoint.created_at and cp.created_at <= checkpoint.created_at:
                    # Create a copy of the checkpoint for the new internal session
                    new_checkpoint = Checkpoint(
                        internal_session_id=agent.internal_session.id,
                        checkpoint_name=cp.checkpoint_name,
                        session_state=cp.session_state.copy(),
                        conversation_history=cp.conversation_history.copy(),
                        is_auto=cp.is_auto,
                        created_at=cp.created_at,
                        metadata=cp.metadata.copy()
                    )
                    checkpoint_repo.create(new_checkpoint)
        
        # Save the restored session
        agent._save_internal_session()
        
        return agent