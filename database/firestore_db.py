"""
Firebase Firestore integration for cross-device session synchronization.
Provides real-time sync of user sessions, BMI data, allergies, and conversation history.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin not installed. Firestore features disabled.")

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Firestore client singleton
_firestore_client = None


def init_firestore() -> Optional[Any]:
    """
    Initialize Firebase Firestore client.
    
    Returns:
        Firestore client instance or None if disabled/unavailable
    """
    global _firestore_client
    
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase Admin SDK not available. Install: pip install firebase-admin")
        return None
    
    use_firestore = os.getenv("USE_FIRESTORE", "false").lower() == "true"
    if not use_firestore:
        logger.info("Firestore disabled in .env (USE_FIRESTORE=false)")
        return None
    
    if _firestore_client is not None:
        return _firestore_client
    
    try:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        
        if not cred_path or not os.path.exists(cred_path):
            logger.error(f"Firebase credentials file not found: {cred_path}")
            logger.info("Download from: Firebase Console → Project Settings → Service Accounts")
            return None
        
        # Initialize Firebase app if not already done
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized successfully")
        
        _firestore_client = firestore.client()
        logger.info("✅ Firestore client connected")
        return _firestore_client
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firestore: {e}")
        return None


def get_firestore_client() -> Optional[Any]:
    """Get the Firestore client instance."""
    return _firestore_client


# ========== Session Management ==========

async def create_firestore_session(
    user_id: str,
    session_id: str,
    expiry_days: int = 7
) -> Dict[str, Any]:
    """
    Create a new user session in Firestore.
    
    Args:
        user_id: User identifier (email, Firebase UID, device ID)
        session_id: Unique session UUID
        expiry_days: Session expiration in days
    
    Returns:
        Session document data
    """
    db = get_firestore_client()
    if not db:
        raise ValueError("Firestore not initialized. Check .env configuration.")
    
    now = datetime.utcnow()
    expires_at = now + timedelta(days=expiry_days)
    
    session_data = {
        "user_id": user_id,
        "session_id": session_id,
        "created_at": now,
        "expires_at": expires_at,
        "last_accessed": now,
        "bmi_data": None,
        "allergies": [],
        "preferences": {},
        "conversation_history": [],
        "daily_tracking": {
            "date": now.strftime("%Y-%m-%d"),
            "total_calories": 0,
            "total_sugar": 0,
            "total_sodium": 0,
            "meals": []
        }
    }
    
    # Store in Firestore
    db.collection("sessions").document(session_id).set(session_data)
    logger.info(f"✅ Firestore session created: {session_id} (user: {user_id})")
    
    return session_data


async def get_firestore_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve session from Firestore.
    
    Args:
        session_id: Session UUID
    
    Returns:
        Session data dict or None if not found/expired
    """
    db = get_firestore_client()
    if not db:
        return None
    
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        session_data = doc.to_dict()
        
        # Check expiration
        expires_at = session_data.get("expires_at")
        if expires_at and expires_at < datetime.utcnow():
            logger.warning(f"Session expired: {session_id}")
            await delete_firestore_session(session_id)
            return None
        
        # Update last accessed
        doc_ref.update({"last_accessed": datetime.utcnow()})
        
        return session_data
        
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        return None


async def update_firestore_session(
    session_id: str,
    update_data: Dict[str, Any]
) -> bool:
    """
    Update session fields in Firestore.
    
    Args:
        session_id: Session UUID
        update_data: Fields to update (e.g., {"bmi_data": {...}, "allergies": [...]})
    
    Returns:
        True if successful
    """
    db = get_firestore_client()
    if not db:
        return False
    
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc_ref.update(update_data)
        logger.info(f"✅ Session updated: {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        return False


async def delete_firestore_session(session_id: str) -> bool:
    """Delete a session from Firestore."""
    db = get_firestore_client()
    if not db:
        return False
    
    try:
        db.collection("sessions").document(session_id).delete()
        logger.info(f"🗑️  Session deleted: {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return False


# ========== Conversation History ==========

async def add_firestore_conversation(
    session_id: str,
    query: str,
    response: str,
    max_history: int = 10
) -> bool:
    """
    Add a conversation turn to Firestore session history.
    
    Args:
        session_id: Session UUID
        query: User query
        response: AI response
        max_history: Maximum conversation turns to keep
    
    Returns:
        True if successful
    """
    db = get_firestore_client()
    if not db:
        return False
    
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.error(f"Session not found: {session_id}")
            return False
        
        session_data = doc.to_dict()
        history = session_data.get("conversation_history", [])
        
        # Add new conversation
        history.append({
            "query": query,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last N messages
        if len(history) > max_history:
            history = history[-max_history:]
        
        doc_ref.update({"conversation_history": history})
        return True
        
    except Exception as e:
        logger.error(f"Error adding conversation to {session_id}: {e}")
        return False


# ========== Daily Tracking ==========

async def update_daily_tracking(
    session_id: str,
    calories: float,
    sugar: float,
    sodium: float,
    meal_description: str
) -> Dict[str, Any]:
    """
    Update daily nutrition tracking in Firestore.
    Resets tracking data if new date is detected.
    
    Args:
        session_id: Session UUID
        calories: Calories consumed
        sugar: Sugar consumed (grams)
        sodium: Sodium consumed (mg)
        meal_description: Description of the meal
    
    Returns:
        Updated daily tracking data
    """
    db = get_firestore_client()
    if not db:
        raise ValueError("Firestore not initialized")
    
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Session not found: {session_id}")
        
        session_data = doc.to_dict()
        daily_tracking = session_data.get("daily_tracking", {})
        
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        tracked_date = daily_tracking.get("date")
        
        # Reset if new day
        if tracked_date != current_date:
            daily_tracking = {
                "date": current_date,
                "total_calories": 0,
                "total_sugar": 0,
                "total_sodium": 0,
                "meals": []
            }
        
        # Add meal
        daily_tracking["total_calories"] += calories
        daily_tracking["total_sugar"] += sugar
        daily_tracking["total_sodium"] += sodium
        daily_tracking["meals"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "description": meal_description,
            "calories": calories,
            "sugar": sugar,
            "sodium": sodium
        })
        
        # Update Firestore
        doc_ref.update({"daily_tracking": daily_tracking})
        
        logger.info(f"📊 Daily tracking updated: {session_id} ({current_date})")
        return daily_tracking
        
    except Exception as e:
        logger.error(f"Error updating daily tracking: {e}")
        raise


async def get_daily_tracking(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get today's nutrition tracking data.
    
    Returns:
        Daily tracking data or None
    """
    db = get_firestore_client()
    if not db:
        return None
    
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        session_data = doc.to_dict()
        daily_tracking = session_data.get("daily_tracking", {})
        
        # Reset if old date
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        if daily_tracking.get("date") != current_date:
            return {
                "date": current_date,
                "total_calories": 0,
                "total_sugar": 0,
                "total_sodium": 0,
                "meals": []
            }
        
        return daily_tracking
        
    except Exception as e:
        logger.error(f"Error getting daily tracking: {e}")
        return None


# ========== Cleanup ==========

async def cleanup_expired_firestore_sessions() -> int:
    """
    Delete expired sessions from Firestore.
    
    Returns:
        Number of sessions deleted
    """
    db = get_firestore_client()
    if not db:
        return 0
    
    try:
        now = datetime.utcnow()
        sessions_ref = db.collection("sessions")
        
        # Query expired sessions
        expired_query = sessions_ref.where("expires_at", "<", now).stream()
        
        deleted_count = 0
        for doc in expired_query:
            doc.reference.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"🗑️  Cleaned up {deleted_count} expired Firestore sessions")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        return 0
