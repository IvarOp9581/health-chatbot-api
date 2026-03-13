"""
Session Service
High-level session management wrapper
"""

from typing import Dict, Optional, List
from database.session_db import (
    create_session,
    get_session,
    update_session,
    add_conversation,
    delete_session,
    delete_expired_sessions,
    get_session_stats
)

class SessionService:
    """Session management service"""
    
    @staticmethod
    async def create_new_session(user_id: Optional[str] = None, expiry_days: int = 7) -> Dict:
        """Create a new user session"""
        return await create_session(user_id, expiry_days)
    
    @staticmethod
    async def get_user_session(session_id: str) -> Optional[Dict]:
        """Retrieve user session data"""
        return await get_session(session_id)
    
    @staticmethod
    async def update_user_bmi(
        session_id: str,
        bmi_data: Dict
    ) -> bool:
        """Update user's BMI data in session"""
        session = await get_session(session_id)
        if not session:
            return False
        
        user_data = session['user_data']
        user_data['bmi_data'] = bmi_data
        
        return await update_session(session_id, user_data)
    
    @staticmethod
    async def update_user_allergies(
        session_id: str,
        allergies: List[str]
    ) -> bool:
        """Update user's allergy list"""
        session = await get_session(session_id)
        if not session:
            return False
        
        user_data = session['user_data']
        user_data['allergies'] = allergies
        
        return await update_session(session_id, user_data)
    
    @staticmethod
    async def update_user_preferences(
        session_id: str,
        preferences: List[str]
    ) -> bool:
        """Update user's dietary preferences"""
        session = await get_session(session_id)
        if not session:
            return False
        
        user_data = session['user_data']
        user_data['preferences'] = preferences
        
        return await update_session(session_id, user_data)
    
    @staticmethod
    async def save_conversation(
        session_id: str,
        query: str,
        response: str,
        max_history: int = 10
    ) -> bool:
        """Save conversation to session history"""
        return await add_conversation(session_id, query, response, max_history)
    
    @staticmethod
    async def get_conversation_history(session_id: str) -> List[Dict]:
        """Get user's conversation history"""
        session = await get_session(session_id)
        if not session:
            return []
        
        return session['user_data'].get('conversation_history', [])
    
    @staticmethod
    async def get_user_context(session_id: str) -> Dict:
        """Get user's health context (BMI, allergies, preferences)"""
        session = await get_session(session_id)
        if not session:
            return {
                "exists": False,
                "bmi_data": None,
                "allergies": [],
                "preferences": []
            }
        
        user_data = session['user_data']
        return {
            "exists": True,
            "bmi_data": user_data.get('bmi_data'),
            "allergies": user_data.get('allergies', []),
            "preferences": user_data.get('preferences', []),
            "conversation_count": len(user_data.get('conversation_history', []))
        }
    
    @staticmethod
    async def delete_user_session(session_id: str) -> bool:
        """Delete a user session"""
        return await delete_session(session_id)
    
    @staticmethod
    async def cleanup_expired_sessions() -> int:
        """Clean up expired sessions (background task)"""
        return await delete_expired_sessions()
    
    @staticmethod
    async def get_stats() -> Dict:
        """Get session statistics"""
        return await get_session_stats()
    
    @staticmethod
    async def update_full_user_data(
        session_id: str,
        bmi_data: Optional[Dict] = None,
        allergies: Optional[List[str]] = None,
        preferences: Optional[List[str]] = None
    ) -> bool:
        """Update multiple user data fields at once"""
        session = await get_session(session_id)
        if not session:
            return False
        
        user_data = session['user_data']
        
        if bmi_data is not None:
            user_data['bmi_data'] = bmi_data
        
        if allergies is not None:
            user_data['allergies'] = allergies
        
        if preferences is not None:
            user_data['preferences'] = preferences
        
        return await update_session(session_id, user_data)

# Create global instance
session_service = SessionService()
