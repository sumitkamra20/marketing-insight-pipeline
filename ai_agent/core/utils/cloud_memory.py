"""
Cloud Memory Storage for Marketing Insight Pipeline
Uses Google Cloud Firestore for persistent conversation memory across container restarts
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore
    from google.cloud.exceptions import NotFound
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("Google Cloud Firestore not available. Install with: pip install google-cloud-firestore")


class CloudMemoryStorage:
    """Cloud-based memory storage using Firestore for conversation persistence."""

    def __init__(self, project_id: Optional[str] = None, collection_name: str = "chat_sessions"):
        """
        Initialize cloud memory storage.

        Args:
            project_id: Google Cloud Project ID (if None, uses default)
            collection_name: Firestore collection name for storing sessions
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.collection_name = collection_name
        self.client = None

        if FIRESTORE_AVAILABLE and self.project_id:
            try:
                self.client = firestore.Client(project=self.project_id)
                logger.info(f"Initialized Firestore client for project: {self.project_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Firestore client: {e}")
                self.client = None
        else:
            logger.warning("Firestore not available or project ID not set")

    def is_available(self) -> bool:
        """Check if cloud memory storage is available."""
        return self.client is not None

    def save_session(self, session_id: str, messages: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save conversation session to Firestore.

        Args:
            session_id: Unique session identifier
            messages: List of conversation messages
            metadata: Optional session metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            session_data = {
                'session_id': session_id,
                'messages': messages,
                'metadata': metadata or {},
                'updated_at': firestore.SERVER_TIMESTAMP,
                'created_at': firestore.SERVER_TIMESTAMP
            }

            # Use merge=True to update existing sessions
            doc_ref = self.client.collection(self.collection_name).document(session_id)
            doc_ref.set(session_data, merge=True)

            logger.info(f"Saved session {session_id[:8]}... with {len(messages)} messages")
            return True

        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation session from Firestore.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dictionary or None if not found
        """
        if not self.is_available():
            return None

        try:
            doc_ref = self.client.collection(self.collection_name).document(session_id)
            doc = doc_ref.get()

            if doc.exists:
                session_data = doc.to_dict()
                logger.info(f"Loaded session {session_id[:8]}... with {len(session_data.get('messages', []))} messages")
                return session_data
            else:
                logger.info(f"Session {session_id[:8]}... not found")
                return None

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete conversation session from Firestore.

        Args:
            session_id: Unique session identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            doc_ref = self.client.collection(self.collection_name).document(session_id)
            doc_ref.delete()

            logger.info(f"Deleted session {session_id[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List recent conversation sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        if not self.is_available():
            return []

        try:
            sessions = []
            docs = self.client.collection(self.collection_name)\
                             .order_by('updated_at', direction=firestore.Query.DESCENDING)\
                             .limit(limit)\
                             .stream()

            for doc in docs:
                data = doc.to_dict()
                sessions.append({
                    'session_id': data.get('session_id'),
                    'message_count': len(data.get('messages', [])),
                    'updated_at': data.get('updated_at'),
                    'created_at': data.get('created_at'),
                    'metadata': data.get('metadata', {})
                })

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old conversation sessions.

        Args:
            days_old: Delete sessions older than this many days

        Returns:
            Number of sessions deleted
        """
        if not self.is_available():
            return 0

        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            # Query old sessions
            old_sessions = self.client.collection(self.collection_name)\
                                    .where('updated_at', '<', cutoff_date)\
                                    .stream()

            deleted_count = 0
            for doc in old_sessions:
                doc.reference.delete()
                deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} sessions older than {days_old} days")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0


# Global instance for easy access
cloud_memory = None

def get_cloud_memory() -> Optional[CloudMemoryStorage]:
    """Get the global cloud memory instance."""
    global cloud_memory

    if cloud_memory is None and os.getenv('USE_CLOUD_MEMORY', 'false').lower() == 'true':
        cloud_memory = CloudMemoryStorage()

    return cloud_memory

def initialize_cloud_memory(project_id: Optional[str] = None) -> CloudMemoryStorage:
    """Initialize cloud memory with specific project ID."""
    global cloud_memory
    cloud_memory = CloudMemoryStorage(project_id)
    return cloud_memory
