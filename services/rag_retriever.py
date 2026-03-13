"""
RAG Retrieval Layer
Intelligently retrieves relevant context before AI call
"""

import re
from typing import Dict, List, Optional
from database.queries import (
    search_foods_by_name,
    get_random_diverse_foods,
    get_foods_by_category
)
from database.guidelines import WHO_GUIDELINES

async def extract_food_names(query: str) -> List[str]:
    """
    Extract potential food names from user query
    Simple regex-based extraction (can be enhanced with NLP)
    """
    # Remove common words
    stop_words = {'i', 'had', 'ate', 'drank', 'drink', 'eat', 'eating', 'drinking', 
                  'a', 'an', 'the', 'some', 'my', 'of', 'with', 'and', 'or', 'much'}
    
    # Extract words (alphanumeric and hyphens)
    words = re.findall(r'\b[a-zA-Z][\w-]*\b', query.lower())
    
    # Filter stop words and keep meaningful food-related terms
    potential_foods = [w for w in words if w not in stop_words and len(w) > 2]
    
    return potential_foods

async def retrieve_foods_from_query(query: str, limit: int = 10) -> List[Dict]:
    """
    Retrieve relevant foods from database based on query
    Uses FTS to find matching foods
    """
    food_names = await extract_food_names(query)
    retrieved_foods = []
    seen_fdc_ids = set()
    
    # Search for each potential food name
    for food_name in food_names:
        results = await search_foods_by_name(food_name, limit=5)
        
        for food in results:
            if food['fdc_id'] not in seen_fdc_ids:
                retrieved_foods.append(food)
                seen_fdc_ids.add(food['fdc_id'])
        
        if len(retrieved_foods) >= limit:
            break
    
    return retrieved_foods[:limit]

async def retrieve_diverse_foods_for_meal_plan(
    exclude_allergens: List[str] = None,
    count: int = 50
) -> List[Dict]:
    """
    Retrieve diverse foods for meal plan generation
    Uses category-based search for variety
    """
    exclude_allergens = exclude_allergens or []
    
    # Define broad food categories for diversity
    categories = [
        "fruit OR fruits",
        "vegetable OR vegetables",
        "meat OR chicken OR beef OR pork",
        "fish OR salmon OR tuna",
        "rice OR pasta OR bread OR grain",
        "milk OR yogurt OR cheese",
        "egg OR eggs",
        "nuts OR seeds",
        "beans OR lentils OR legumes"
    ]
    
    # Get foods from each category
    foods = await get_foods_by_category(
        categories=categories,
        exclude_keywords=exclude_allergens,
        limit_per_category=6
    )
    
    # If not enough, add random foods
    if len(foods) < count:
        random_foods = await get_random_diverse_foods(
            count=count - len(foods),
            exclude_keywords=exclude_allergens
        )
        foods.extend(random_foods)
    
    return foods[:count]

def determine_query_type(query: str) -> str:
    """
    Determine the type of health query
    Returns: 'sugar_check', 'diet_plan', 'allergy', 'bmi', 'general'
    """
    query_lower = query.lower()
    
    # Diet plan keywords
    if any(word in query_lower for word in ['diet', 'meal plan', 'menu', 'calories', 'weight']):
        if any(word in query_lower for word in ['lose', 'gain', 'maintain', 'bulk', 'cut']):
            return 'diet_plan'
    
    # Sugar/nutrition check keywords
    if any(word in query_lower for word in ['sugar', 'sweet', 'soda', 'candy', 'dessert', 
                                               'drank', 'ate', 'had', 'consumed']):
        return 'sugar_check'
    
    # BMI keywords
    if any(word in query_lower for word in ['bmi', 'weight', 'height', 'overweight', 'obese']):
        return 'bmi'
    
    # Allergy keywords
    if any(word in query_lower for word in ['allerg', 'substitute', 'replace', 'alternative', 
                                               'instead of', 'intolerant']):
        return 'allergy'
    
    return 'general'

async def get_relevant_who_guidelines(query_type: str) -> Dict:
    """
    Get WHO guidelines relevant to query type
    """
    if query_type == 'sugar_check':
        return {
            "free_sugars": WHO_GUIDELINES["FREE_SUGARS"],
            "message": "WHO recommends less than 50g/day (10% energy), ideally less than 25g/day (5% energy)."
        }
    
    elif query_type == 'diet_plan':
        return {
            "fruits_vegetables": WHO_GUIDELINES["FRUITS_VEGETABLES"],
            "free_sugars": WHO_GUIDELINES["FREE_SUGARS"],
            "fats": WHO_GUIDELINES["FATS"],
            "salt_sodium": WHO_GUIDELINES["SALT_SODIUM"],
            "message": "Balanced diet should include 400g fruits/vegetables daily, <50g sugar, <30% energy from fats, <5g salt."
        }
    
    elif query_type == 'bmi':
        return {
            "bmi_categories": "Underweight: <18.5, Normal: 18.5-24.9, Overweight: 25-29.9, Obese: ≥30",
            "message": "BMI is a screening tool. Consult healthcare provider for personalized advice."
        }
    
    else:
        return {
            "general": WHO_GUIDELINES,
            "message": "WHO promotes healthy eating: fruits, vegetables, whole grains, limited sugar, salt, and unhealthy fats."
        }

async def retrieve_context_for_query(
    query: str,
    user_context: Optional[Dict] = None
) -> Dict:
    """
    Main RAG retrieval function
    Returns comprehensive context for AI processing
    """
    query_type = determine_query_type(query)
    
    # Retrieve relevant foods
    matched_foods = []
    if query_type in ['sugar_check', 'general']:
        matched_foods = await retrieve_foods_from_query(query, limit=10)
    elif query_type == 'diet_plan':
        exclude_allergens = []
        if user_context and user_context.get('allergies'):
            exclude_allergens = user_context['allergies']
        matched_foods = await retrieve_diverse_foods_for_meal_plan(
            exclude_allergens=exclude_allergens,
            count=50
        )
    
    # Get relevant WHO guidelines
    who_guidelines = await get_relevant_who_guidelines(query_type)
    
    # Build context object
    context = {
        "query_type": query_type,
        "matched_foods": matched_foods,
        "food_count": len(matched_foods),
        "who_guidelines": who_guidelines,
        "user_context": user_context or {},
        "retrieval_summary": f"Retrieved {len(matched_foods)} relevant food items from database."
    }
    
    return context
