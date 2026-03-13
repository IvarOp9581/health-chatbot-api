"""
Pydantic Models for Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Session Models
class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: str
    expires_at: str

# BMI Models
class BMICalculateRequest(BaseModel):
    session_id: str
    age: int = Field(..., ge=1, le=120, description="Age in years")
    height_cm: float = Field(..., gt=0, le=300, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, le=500, description="Weight in kilograms")
    gender: str = Field(..., description="Gender: 'male' or 'female'")
    activity_level: Optional[str] = Field("moderate", description="Activity level: sedentary, light, moderate, active, very_active")
    goal: Optional[str] = Field("maintain", description="Goal: lose, lose_fast, maintain, gain, gain_bulk")

class BMIResponse(BaseModel):
    bmi: float
    category: str
    color: str
    bmr: float
    tdee: float
    target_calories: float
    goal: str
    activity_level: str
    macros: Dict
    recommendations: Dict

# Query Models
class HealthQueryRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=1000)

class HealthQueryResponse(BaseModel):
    session_id: str
    query: str
    response_text: str
    query_type: str
    matched_foods_count: int
    api_used: str
    warnings: Optional[Dict] = None

# Diet Plan Models
class DietPlanRequest(BaseModel):
    session_id: str
    goal: str = Field(..., description="Goal: lose, maintain, gain")
    allergies: Optional[List[str]] = Field(default_factory=list)
    preferences: Optional[List[str]] = Field(default_factory=list)

class DietPlanResponse(BaseModel):
    session_id: str
    goal: str
    target_calories: float
    meal_plan: str
    foods_considered: int
    excluded_allergens: List[str]
    api_used: str
    metadata: Dict

# Food Search Models
class FoodSearchResponse(BaseModel):
    query: str
    foods: List[Dict]
    count: int

# Allergy Models
class AllergySubstitutionRequest(BaseModel):
    session_id: str
    original_food: str
    allergens: List[str]

class AllergySubstitutionResponse(BaseModel):
    found: bool
    original_food: Optional[Dict] = None
    alternatives_found: int
    top_alternatives: List[Dict]
    ai_recommendation: str
    allergens_excluded: List[str]
    api_used: str

# Session Update Models
class AllergyUpdateRequest(BaseModel):
    session_id: str
    allergies: List[str]

class PreferenceUpdateRequest(BaseModel):
    session_id: str
    preferences: List[str]

# Health Check Response
class HealthCheckResponse(BaseModel):
    status: str
    database: Dict
    ai_clients: Dict
    sessions: Dict
