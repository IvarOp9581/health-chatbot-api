"""
Health Chatbot Backend - FastAPI Application
Production-ready REST API with RAG + AI Failover
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import asyncio

# Import models
from app.models import *

# Import database
from database.db import init_db, close_db
from database.session_db import init_session_table
from database.firestore_db import init_firestore
from database.queries import get_database_stats, search_foods_by_name

# Import services
from services.ai_client import get_ai_manager
from services.health_calculator import calculate_full_health_profile
from services.nutrition_service import analyze_food_intake
from services.diet_planner import generate_meal_plan
from services.allergy_handler import substitute_food
from services.session_service_hybrid import session_service
from services.rag_retriever import retrieve_context_for_query
from services.prompt_builder import build_prompt

# Load environment variables
load_dotenv()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Background task for session cleanup
async def cleanup_sessions_task():
    """Background task to cleanup expired sessions every hour"""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        try:
            deleted_count = await session_service.cleanup_expired_sessions()
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} expired sessions")
        except Exception as e:
            print(f"❌ Session cleanup error: {e}")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Starting Health Chatbot Backend...")
    
    # Initialize database (with auto-migration on Vercel)
    try:
        await init_db()
        await init_session_table()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        # On Vercel, this is critical - re-raise
        if os.environ.get('VERCEL'):
            raise
    
    # Initialize Firestore (if enabled)
    try:
        init_firestore()
    except Exception as e:
        print(f"⚠️  Firestore initialization error: {e}")
    
    # Initialize AI clients
    try:
        ai_manager = get_ai_manager()
        print(f"🤖 AI Status: {ai_manager.get_status()}")
    except Exception as e:
        print(f"⚠️  AI initialization error: {e}")
    
    # Start background tasks (not on Vercel)
    cleanup_task = None
    if not os.environ.get('VERCEL'):
        cleanup_task = asyncio.create_task(cleanup_sessions_task())
        print("🔄 Background tasks started")
    
    print("✅ Server ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if cleanup_task:
        cleanup_task.cancel()
    try:
        await close_db()
    except:
        pass
    print("👋 Goodbye!")

# Create FastAPI app
app = FastAPI(
    title="Health Chatbot Backend API",
    description="RAG-powered health and nutrition chatbot with Gemini/Groq AI failover",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    print(f"❌ Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )

# ============== ENDPOINTS ==============

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Health Chatbot Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint - returns system status"""
    try:
        db_stats = await get_database_stats()
        ai_manager = get_ai_manager()
        session_stats = await session_service.get_stats()
        
        return {
            "status": "healthy",
            "database": db_stats,
            "ai_clients": ai_manager.get_status(),
            "sessions": session_stats
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============== SESSION ENDPOINTS ==============

@app.post("/api/session", response_model=SessionCreateResponse, tags=["Session"])
@limiter.limit("10/minute")
async def create_session(request: Request):
    """Create a new user session"""
    try:
        session_data = await session_service.create_new_session()
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}", tags=["Session"])
@limiter.limit("20/minute")
async def get_session_info(request: Request, session_id: str):
    """Get session information"""
    session = await session_service.get_user_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return session

@app.delete("/api/session/{session_id}", tags=["Session"])
@limiter.limit("10/minute")
async def delete_session_endpoint(request: Request, session_id: str):
    """Delete a session"""
    success = await session_service.delete_user_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully", "session_id": session_id}

# ============== BMI ENDPOINTS ==============

@app.post("/api/bmi", response_model=BMIResponse, tags=["Health Calculations"])
@limiter.limit("20/minute")
async def calculate_bmi(request: Request, bmi_request: BMICalculateRequest):
    """Calculate BMI and daily calorie needs"""
    try:
        # Validate session
        session = await session_service.get_user_session(bmi_request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate health profile
        health_profile = calculate_full_health_profile(
            weight_kg=bmi_request.weight_kg,
            height_cm=bmi_request.height_cm,
            age=bmi_request.age,
            gender=bmi_request.gender,
            activity_level=bmi_request.activity_level,
            goal=bmi_request.goal
        )
        
        # Save to session
        await session_service.update_user_bmi(bmi_request.session_id, health_profile)
        
        return health_profile
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== QUERY ENDPOINT (Main RAG Chatbot) ==============

@app.post("/api/query", response_model=HealthQueryResponse, tags=["Chatbot"])
@limiter.limit("20/minute")
async def health_query(request: Request, query_request: HealthQueryRequest):
    """Main chatbot endpoint - RAG-powered health queries"""
    try:
        # Get session context
        user_context = await session_service.get_user_context(query_request.session_id)
        
        if not user_context:
            # Create session if it doesn't exist
            await session_service.create_new_session()
            user_context = {"bmi_data": None, "allergies": [], "preferences": [], "conversation_history": []}
        
        # RAG: Retrieve relevant context
        context = await retrieve_context_for_query(
            query_request.query,
            user_context=user_context
        )
        
        # Build prompt with context
        prompt = await build_prompt(query_request.query, context)
        
        # Get AI response with failover
        ai_manager = get_ai_manager()
        response_text, api_used = await ai_manager.get_ai_response(prompt)
        
        # Save conversation
        await session_service.save_conversation(
            query_request.session_id,
            query_request.query,
            response_text
        )
        
        return {
            "session_id": query_request.session_id,
            "query": query_request.query,
            "response_text": response_text,
            "query_type": context['query_type'],
            "matched_foods_count": context['food_count'],
            "api_used": api_used,
            "warnings": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== DIET PLAN ENDPOINT ==============

@app.post("/api/diet-plan", response_model=DietPlanResponse, tags=["Diet Planning"])
@limiter.limit("10/minute")
async def generate_diet_plan(request: Request, plan_request: DietPlanRequest):
    """Generate personalized meal plan with RAG"""
    try:
        # Get session with BMI data
        user_context = await session_service.get_user_context(plan_request.session_id)
        
        if not user_context or not user_context.get('bmi_data'):
            raise HTTPException(
                status_code=400,
                detail="BMI data required. Please calculate BMI first using /api/bmi"
            )
        
        # Update allergies if provided
        if plan_request.allergies:
            await session_service.update_user_allergies(
                plan_request.session_id,
                plan_request.allergies
            )
        
        # Update preferences if provided
        if plan_request.preferences:
            await session_service.update_user_preferences(
                plan_request.session_id,
                plan_request.preferences
            )
        
        # Generate meal plan
        meal_plan = await generate_meal_plan(
            session_id=plan_request.session_id,
            bmi_data=user_context['bmi_data'],
            goal=plan_request.goal,
            allergies=plan_request.allergies,
            preferences=plan_request.preferences
        )
        
        return meal_plan
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== FOOD SEARCH ENDPOINT ==============

@app.get("/api/food/search", response_model=FoodSearchResponse, tags=["Food Database"])
@limiter.limit("30/minute")
async def search_food(
    request: Request,
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """Search foods in database using FTS"""
    try:
        foods = await search_foods_by_name(q, limit=limit)
        
        return {
            "query": q,
            "foods": foods,
            "count": len(foods)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== ALLERGY ENDPOINTS ==============

@app.post("/api/allergy/substitute", response_model=AllergySubstitutionResponse, tags=["Allergies"])
@limiter.limit("15/minute")
async def get_food_substitution(request: Request, sub_request: AllergySubstitutionRequest):
    """Get AI-powered food substitution for allergies"""
    try:
        # Validate session
        session = await session_service.get_user_session(sub_request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get substitution
        result = await substitute_food(
            original_food_name=sub_request.original_food,
            allergens=sub_request.allergens
        )
        
        if not result['found']:
            raise HTTPException(status_code=404, detail=result.get('message', 'No alternatives found'))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/session/allergies", tags=["Session"])
@limiter.limit("10/minute")
async def update_allergies(request: Request, allergy_request: AllergyUpdateRequest):
    """Update user's allergy list"""
    success = await session_service.update_user_allergies(
        allergy_request.session_id,
        allergy_request.allergies
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "message": "Allergies updated successfully",
        "session_id": allergy_request.session_id,
        "allergies": allergy_request.allergies
    }

@app.put("/api/session/preferences", tags=["Session"])
@limiter.limit("10/minute")
async def update_preferences(request: Request, pref_request: PreferenceUpdateRequest):
    """Update user's dietary preferences"""
    success = await session_service.update_user_preferences(
        pref_request.session_id,
        pref_request.preferences
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "message": "Preferences updated successfully",
        "session_id": pref_request.session_id,
        "preferences": pref_request.preferences
    }

# ============== DAILY TRACKING ==============

@app.get("/api/daily-intake/{session_id}", tags=["Daily Tracking"])
@limiter.limit("30/minute")
async def get_daily_intake(request: Request, session_id: str):
    """Get today's nutrition tracking (calories, sugar, sodium totals)"""
    try:
        tracking = await session_service.get_daily_intake(session_id)
        
        if not tracking:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add WHO comparison
        from database.guidelines import WHO_GUIDELINES
        
        FREE_SUGARS = WHO_GUIDELINES["FREE_SUGARS"]
        SALT_SODIUM = WHO_GUIDELINES["SALT_SODIUM"]
        
        who_status = {
            "sugar": {
                "consumed": tracking.get("total_sugar", 0),
                "daily_max": FREE_SUGARS["recommended_max_g"],
                "daily_optimal": FREE_SUGARS["optimal_max_g"],
                "percentage_of_max": round((tracking.get("total_sugar", 0) / FREE_SUGARS["recommended_max_g"]) * 100, 1),
                "status": "safe" if tracking.get("total_sugar", 0) < FREE_SUGARS["optimal_max_g"] 
                          else ("warning" if tracking.get("total_sugar", 0) < FREE_SUGARS["recommended_max_g"] 
                          else "exceeded")
            },
            "sodium": {
                "consumed": tracking.get("total_sodium", 0),
                "daily_max": SALT_SODIUM["sodium_max_mg"],
                "percentage_of_max": round((tracking.get("total_sodium", 0) / SALT_SODIUM["sodium_max_mg"]) * 100, 1),
                "status": "safe" if tracking.get("total_sodium", 0) < SALT_SODIUM["sodium_max_mg"] else "exceeded"
            }
        }
        
        return {
            "session_id": session_id,
            "date": tracking.get("date"),
            "total_calories": tracking.get("total_calories", 0),
            "total_sugar": tracking.get("total_sugar", 0),
            "total_sodium": tracking.get("total_sodium", 0),
            "meals_count": len(tracking.get("meals", [])),
            "meals": tracking.get("meals", []),
            "who_status": who_status,
            "warnings": tracking.get("who_warnings", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/daily-intake/log", tags=["Daily Tracking"])
@limiter.limit("20/minute")
async def log_food_intake(request: Request, log_request: dict):
    """
    Manually log food intake for daily tracking.
    
    Request body:
    {
        "session_id": "uuid",
        "food_description": "500ml Coca-Cola",
        "quantity": 500,
        "unit": "ml"
    }
    """
    try:
        session_id = log_request.get("session_id")
        food_description = log_request.get("food_description")
        quantity = log_request.get("quantity", 1)
        unit = log_request.get("unit", "serving")
        
        if not session_id or not food_description:
            raise HTTPException(
                status_code=400,
                detail="session_id and food_description are required"
            )
        
        # Analyze nutrition
        from services.nutrition_service import analyze_food_intake
        analysis = await analyze_food_intake(food_description, quantity, unit)
        
        if not analysis["found"]:
            raise HTTPException(
                status_code=404,
                detail=f"Food not found in database: {food_description}"
            )
        
        # Update daily tracking
        tracking = await session_service.update_daily_intake(
            session_id=session_id,
            calories=analysis["nutrition"]["calories"],
            sugar=analysis["nutrition"]["sugar_g"],
            sodium=analysis["nutrition"]["sodium_mg"],
            meal_description=f"{quantity}{unit} {food_description}"
        )
        
        return {
            "message": "Food intake logged successfully",
            "session_id": session_id,
            "food": analysis["food"]["description"],
            "nutrition": analysis["nutrition"],
            "daily_totals": {
                "calories": tracking["total_calories"],
                "sugar": tracking["total_sugar"],
                "sodium": tracking["total_sodium"]
            },
            "warnings": tracking.get("who_warnings", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== RUN ==============

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
