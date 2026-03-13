"""
Diet Plan Generator Service
RAG-powered personalized meal plan generation
"""

from typing import Dict, List
from services.rag_retriever import retrieve_diverse_foods_for_meal_plan
from services.ai_client import get_ai_manager
from services.prompt_builder import build_diet_plan_prompt

async def generate_meal_plan(
    session_id: str,
    bmi_data: Dict,
    goal: str = "maintain",
    allergies: List[str] = None,
    preferences: List[str] = None
) -> Dict:
    """
    Generate personalized meal plan using RAG
    
    Args:
        session_id: User session ID
        bmi_data: BMI and calorie data from health_calculator
        goal: 'lose', 'maintain', 'gain'
        allergies: List of allergens to exclude
        preferences: Dietary preferences (vegetarian, etc.)
    
    Returns:
        Complete meal plan with macros
    """
    allergies = allergies or []
    preferences = preferences or []
    
    # Retrieve diverse foods excluding allergens
    foods = await retrieve_diverse_foods_for_meal_plan(
        exclude_allergens=allergies,
        count=50
    )
    
    # Build context for RAG
    context = {
        "query_type": "diet_plan",
        "matched_foods": foods,
        "who_guidelines": {
            "fruits_vegetables": {"daily_min_g": 400, "portions_per_day": 5},
            "free_sugars": {"recommended_max_g": 50, "optimal_max_g": 25},
            "fats": {"total_fat_max_pct": 30, "saturated_fat_max_pct": 10},
            "salt_sodium": {"salt_max_g": 5, "sodium_max_mg": 2000}
        },
        "user_context": {
            "bmi_data": bmi_data,
            "allergies": allergies,
            "preferences": preferences,
            "goal": goal
        }
    }
    
    # Build prompt
    prompt = build_diet_plan_prompt(goal, context)
    
    # Get AI response with failover
    ai_manager = get_ai_manager()
    response, api_used = await ai_manager.get_ai_response(prompt)
    
    # Parse response (basic parsing - can be enhanced)
    return {
        "session_id": session_id,
        "goal": goal,
        "target_calories": bmi_data.get('target_calories', 0),
        "meal_plan": response,
        "raw_response": response,
        "foods_considered": len(foods),
        "excluded_allergens": allergies,
        "api_used": api_used,
        "metadata": {
            "bmi": bmi_data.get('bmi'),
            "bmi_category": bmi_data.get('category'),
            "activity_level": bmi_data.get('activity_level', 'moderate')
        }
    }

async def generate_quick_meal_suggestions(
    meal_type: str,  # 'breakfast', 'lunch', 'dinner', 'snack'
    calorie_target: int,
    allergies: List[str] = None
) -> Dict:
    """
    Generate quick meal suggestions for a specific meal type
    """
    allergies = allergies or []
    
    # Get relevant foods
    if meal_type == 'breakfast':
        category = "breakfast OR egg OR oatmeal OR cereal OR yogurt"
    elif meal_type == 'lunch':
        category = "sandwich OR salad OR soup OR rice OR pasta"
    elif meal_type == 'dinner':
        category = "chicken OR fish OR beef OR vegetables OR rice"
    else:  # snack
        category = "fruit OR nuts OR yogurt OR granola"
    
    from database.queries import get_foods_by_category
    foods = await get_foods_by_category(
        categories=[category],
        exclude_keywords=allergies,
        limit_per_category=10
    )
    
    # Filter by calorie range (±100 of target)
    suitable_foods = [
        f for f in foods
        if abs((f['calories'] or 0) - calorie_target) <= 100
    ]
    
    return {
        "meal_type": meal_type,
        "calorie_target": calorie_target,
        "suggestions": suitable_foods[:5],
        "total_suggestions": len(suitable_foods)
    }

async def validate_meal_plan(meal_plan_text: str, target_calories: int) -> Dict:
    """
    Validate that a meal plan meets nutritional targets
    (Can be enhanced with actual parsing and calculation)
    """
    # Basic validation - check if plan mentions key elements
    has_breakfast = "breakfast" in meal_plan_text.lower()
    has_lunch = "lunch" in meal_plan_text.lower()
    has_dinner = "dinner" in meal_plan_text.lower()
    
    has_calories = "kcal" in meal_plan_text.lower() or "calorie" in meal_plan_text.lower()
    has_macros = any(word in meal_plan_text.lower() for word in ["protein", "carb", "fat"])
    
    is_valid = all([has_breakfast, has_lunch, has_dinner, has_calories])
    
    return {
        "is_valid": is_valid,
        "has_all_meals": has_breakfast and has_lunch and has_dinner,
        "has_nutritional_info": has_calories and has_macros,
        "completeness_score": sum([
            has_breakfast, has_lunch, has_dinner, has_calories, has_macros
        ]) / 5 * 100
    }
