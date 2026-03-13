"""
Hybrid Session Service
Supports both SQLite (local testing) and Firestore (production cross-device sync)
"""

import os
import logging
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv

# Import both backends
from database.session_db import (
    create_session as sqlite_create_session,
    get_session as sqlite_get_session,
    update_session as sqlite_update_session,
    add_conversation as sqlite_add_conversation,
    delete_session as sqlite_delete_session,
    delete_expired_sessions as sqlite_delete_expired_sessions,
    get_session_stats as sqlite_get_session_stats
)

from database.firestore_db import (
    init_firestore,
    get_firestore_client,
    create_firestore_session,
    get_firestore_session,
    update_firestore_session,
    delete_firestore_session,
    add_firestore_conversation,
    cleanup_expired_firestore_sessions,
    update_daily_tracking,
    get_daily_tracking
)

load_dotenv()

logger = logging.getLogger(__name__)

# Determine backend
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true"


class HybridSessionService:
    """
    Unified session service supporting both SQLite and Firestore.
    
    - SQLite: Fast local storage, good for MVP and testing
    - Firestore: Cloud sync, survives app reinstalls, works across devices
    """
    
    def __init__(self):
        self.use_firestore = USE_FIRESTORE
        
        if self.use_firestore:
            init_firestore()
            if get_firestore_client():
                logger.info("✅ Using Firestore for session management")
            else:
                logger.warning("❌ Firestore failed, falling back to SQLite")
                self.use_firestore = False
        else:
            logger.info("✅ Using SQLite for session management")
    
    async def create_new_session(
        self,
        user_id: Optional[str] = None,
        expiry_days: int = 7
    ) -> Dict:
        """Create a new user session"""
        if self.use_firestore and get_firestore_client():
            # Generate session ID first
            temp_session = await sqlite_create_session(user_id, expiry_days)
            session_id = temp_session['session_id']
            
            # Create in Firestore
            session_data = await create_firestore_session(
                user_id=user_id or "anonymous",
                session_id=session_id,
                expiry_days=expiry_days
            )
            
            return {
                "session_id": session_id,
                "user_id": session_data.get("user_id"),
                "expires_at": session_data.get("expires_at").isoformat(),
                "backend": "firestore"
            }
        else:
            # Use SQLite
            result = await sqlite_create_session(user_id, expiry_days)
            result["backend"] = "sqlite"
            return result
    
    async def get_user_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve user session data"""
        if self.use_firestore and get_firestore_client():
            return await get_firestore_session(session_id)
        else:
            return await sqlite_get_session(session_id)
    
    async def update_user_bmi(
        self,
        session_id: str,
        bmi_data: Dict
    ) -> bool:
        """Update user's BMI data in session"""
        if self.use_firestore and get_firestore_client():
            return await update_firestore_session(
                session_id,
                {"bmi_data": bmi_data}
            )
        else:
            session = await sqlite_get_session(session_id)
            if not session:
                return False
            
            user_data = session['user_data']
            user_data['bmi_data'] = bmi_data
            
            return await sqlite_update_session(session_id, user_data)
    
    async def update_user_allergies(
        self,
        session_id: str,
        allergies: List[str]
    ) -> bool:
        """Update user's allergy list"""
        if self.use_firestore and get_firestore_client():
            return await update_firestore_session(
                session_id,
                {"allergies": allergies}
            )
        else:
            session = await sqlite_get_session(session_id)
            if not session:
                return False
            
            user_data = session['user_data']
            user_data['allergies'] = allergies
            
            return await sqlite_update_session(session_id, user_data)
    
    async def update_user_preferences(
        self,
        session_id: str,
        preferences: List[str]
    ) -> bool:
        """Update user's dietary preferences"""
        if self.use_firestore and get_firestore_client():
            return await update_firestore_session(
                session_id,
                {"preferences": preferences}
            )
        else:
            session = await sqlite_get_session(session_id)
            if not session:
                return False
            
            user_data = session['user_data']
            user_data['preferences'] = preferences
            
            return await sqlite_update_session(session_id, user_data)
    
    async def save_conversation(
        self,
        session_id: str,
        query: str,
        response: str,
        max_history: int = 10
    ) -> bool:
        """Save conversation history"""
        if self.use_firestore and get_firestore_client():
            return await add_firestore_conversation(
                session_id,
                query,
                response,
                max_history
            )
        else:
            return await sqlite_add_conversation(
                session_id,
                query,
                response,
                max_history
            )
    
    async def get_conversation_history(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation history"""
        session = await self.get_user_session(session_id)
        if not session:
            return None
        
        if self.use_firestore:
            return session.get('conversation_history', [])
        else:
            return session['user_data'].get('conversation_history', [])
    
    async def get_user_context(self, session_id: str) -> Optional[Dict]:
        """Get full user context (BMI, allergies, preferences)"""
        session = await self.get_user_session(session_id)
        if not session:
            return None
        
        if self.use_firestore:
            return {
                'bmi_data': session.get('bmi_data'),
                'allergies': session.get('allergies', []),
                'preferences': session.get('preferences', {}),
                'conversation_history': session.get('conversation_history', [])
            }
        else:
            return session['user_data']
    
    async def delete_user_session(self, session_id: str) -> bool:
        """Delete a user session"""
        if self.use_firestore and get_firestore_client():
            return await delete_firestore_session(session_id)
        else:
            return await sqlite_delete_session(session_id)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        if self.use_firestore and get_firestore_client():
            return await cleanup_expired_firestore_sessions()
        else:
            return await sqlite_delete_expired_sessions()
    
    async def get_stats(self) -> Dict:
        """Get session statistics"""
        if self.use_firestore and get_firestore_client():
            # Firestore stats
            db = get_firestore_client()
            sessions_ref = db.collection("sessions")
            
            all_sessions = sessions_ref.stream()
            total = sum(1 for _ in all_sessions)
            
            return {
                "backend": "firestore",
                "total_sessions": total,
                "active_sessions": total  # Firestore auto-cleans
            }
        else:
            stats = await sqlite_get_session_stats()
            stats["backend"] = "sqlite"
            return stats
    
    # ========== Daily Tracking (Firestore Only) ==========
    
    async def update_daily_intake(
        self,
        session_id: str,
        calories: float,
        sugar: float,
        sodium: float,
        meal_description: str
    ) -> Dict[str, Any]:
        """
        Update daily nutrition tracking.
        
        Args:
            session_id: Session UUID
            calories: Calories consumed
            sugar: Sugar in grams
            sodium: Sodium in mg
            meal_description: Description of the meal
        
        Returns:
            Updated daily tracking data with totals and WHO warnings
        """
        if self.use_firestore and get_firestore_client():
            tracking = await update_daily_tracking(
                session_id,
                calories,
                sugar,
                sodium,
                meal_description
            )
            
            # Add WHO warnings
            from database.guidelines import FREE_SUGARS, SALT_SODIUM
            
            warnings = []
            if tracking["total_sugar"] > FREE_SUGARS["daily_max_grams"]:
                warnings.append(f"⚠️ Sugar intake ({tracking['total_sugar']:.1f}g) exceeds WHO daily limit ({FREE_SUGARS['daily_max_grams']}g)")
            elif tracking["total_sugar"] > FREE_SUGARS["daily_optimal_grams"]:
                warnings.append(f"⚠️ Sugar intake ({tracking['total_sugar']:.1f}g) exceeds WHO optimal limit ({FREE_SUGARS['daily_optimal_grams']}g)")
            
            if tracking["total_sodium"] > SALT_SODIUM["daily_max_mg"]:
                warnings.append(f"⚠️ Sodium intake ({tracking['total_sodium']:.0f}mg) exceeds WHO daily limit ({SALT_SODIUM['daily_max_mg']}mg)")
            
            tracking["who_warnings"] = warnings
            return tracking
        else:
            # SQLite fallback: basic tracking in user_data
            session = await sqlite_get_session(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            user_data = session['user_data']
            
            # Simple daily tracking
            from datetime import datetime
            current_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            if 'daily_tracking' not in user_data or user_data['daily_tracking'].get('date') != current_date:
                user_data['daily_tracking'] = {
                    "date": current_date,
                    "total_calories": 0,
                    "total_sugar": 0,
                    "total_sodium": 0,
                    "meals": []
                }
            
            user_data['daily_tracking']['total_calories'] += calories
            user_data['daily_tracking']['total_sugar'] += sugar
            user_data['daily_tracking']['total_sodium'] += sodium
            user_data['daily_tracking']['meals'].append({
                "timestamp": datetime.utcnow().isoformat(),
                "description": meal_description,
                "calories": calories,
                "sugar": sugar,
                "sodium": sodium
            })
            
            await sqlite_update_session(session_id, user_data)
            return user_data['daily_tracking']
    
    async def get_daily_intake(self, session_id: str) -> Optional[Dict]:
        """Get today's nutrition tracking"""
        if self.use_firestore and get_firestore_client():
            return await get_daily_tracking(session_id)
        else:
            session = await sqlite_get_session(session_id)
            if not session:
                return None
            
            from datetime import datetime
            current_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            tracking = session['user_data'].get('daily_tracking', {})
            
            # Reset if old date
            if tracking.get('date') != current_date:
                return {
                    "date": current_date,
                    "total_calories": 0,
                    "total_sugar": 0,
                    "total_sodium": 0,
                    "meals": []
                }
            
            return tracking


# Global singleton instance
session_service = HybridSessionService()
