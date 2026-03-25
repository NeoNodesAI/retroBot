"""Database models for conversation history."""
from typing import Optional, Dict, List
from datetime import datetime


class Conversation:
    """Conversation model."""
    
    def __init__(
        self,
        session_id: str,
        messages: List[Dict],
        user_context: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.session_id = session_id
        self.messages = messages
        self.user_context = user_context or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "user_context": self.user_context,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

