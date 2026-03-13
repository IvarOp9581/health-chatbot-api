"""
Session Database Operations
Persistent user session storage in SQLite
"""

import aiosqlite
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "health_data.db"

async def init_session_table():
    """Create session table if it doesn't exist"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for cleanup queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON user_sessions(expires_at)
        """)
        
        await db.commit()

async def create_session(user_id: Optional[str] = None, expiry_days: int = 7) -> Dict:
    """
    Create a new user session
    Returns session_id and expiry details
    """
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=expiry_days)
    
    user_data = {
        "user_id": user_id,
        "bmi_data": None,
        "allergies": [],
        "preferences": [],
        "conversation_history": []
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_sessions (session_id, user_data, created_at, expires_at, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, json.dumps(user_data), created_at.isoformat(), 
              expires_at.isoformat(), created_at.isoformat()))
        
        await db.commit()
    
    return {
        "session_id": session_id,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat()
    }

async def get_session(session_id: str) -> Optional[Dict]:
    """
    Retrieve session data
    Returns None if session doesn't exist or expired
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute("""
            SELECT session_id, user_data, created_at, expires_at, last_accessed
            FROM user_sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Check if expired
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires_at:
            await delete_session(session_id)
            return None
        
        # Update last accessed
        await db.execute("""
            UPDATE user_sessions 
            SET last_accessed = ?
            WHERE session_id = ?
        """, (datetime.utcnow().isoformat(), session_id))
        await db.commit()
        
        return {
            "session_id": row["session_id"],
            "user_data": json.loads(row["user_data"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "last_accessed": row["last_accessed"]
        }

async def update_session(session_id: str, user_data: Dict) -> bool:
    """
    Update session user_data
    Returns True if successful, False if session doesn't exist
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            UPDATE user_sessions
            SET user_data = ?, last_accessed = ?
            WHERE session_id = ?
        """, (json.dumps(user_data), datetime.utcnow().isoformat(), session_id))
        
        await db.commit()
        return cursor.rowcount > 0

async def add_conversation(session_id: str, query: str, response: str, max_history: int = 10) -> bool:
    """
    Add conversation to session history
    Keeps only last max_history conversations
    """
    session = await get_session(session_id)
    if not session:
        return False
    
    user_data = session["user_data"]
    conversation_history = user_data.get("conversation_history", [])
    
    # Add new conversation
    conversation_history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "response": response
    })
    
    # Keep only last N conversations
    if len(conversation_history) > max_history:
        conversation_history = conversation_history[-max_history:]
    
    user_data["conversation_history"] = conversation_history
    
    return await update_session(session_id, user_data)

async def delete_session(session_id: str) -> bool:
    """Delete a session"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM user_sessions WHERE session_id = ?
        """, (session_id,))
        
        await db.commit()
        return cursor.rowcount > 0

async def delete_expired_sessions() -> int:
    """
    Delete all expired sessions
    Returns number of deleted sessions
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM user_sessions 
            WHERE expires_at < ?
        """, (datetime.utcnow().isoformat(),))
        
        await db.commit()
        return cursor.rowcount

async def get_session_stats() -> Dict:
    """Get session statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM user_sessions")
        total_sessions = (await cursor.fetchone())[0]
        
        cursor = await db.execute("""
            SELECT COUNT(*) FROM user_sessions 
            WHERE expires_at > ?
        """, (datetime.utcnow().isoformat(),))
        active_sessions = (await cursor.fetchone())[0]
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions
        }
