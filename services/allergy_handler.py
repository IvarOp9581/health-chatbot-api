"""
Allergy Handler Service
Food substitution and allergen management
"""

from typing import Dict, List
from database.queries import find_similar_foods, search_foods_by_name
from services.ai_client import get_ai_manager
from services.prompt_builder import build_allergy_substitution_prompt

# Common allergen keywords mapping
ALLERGEN_KEYWORDS = {
    "dairy": ["milk", "cheese", "yogurt", "curd", "butter", "cream", "whey", "casein", "lactose"],
    "nuts": ["peanut", "almond", "cashew", "walnut", "pecan", "hazelnut", "pistachio", "macadamia"],
    "tree_nuts": ["almond", "cashew", "walnut", "pecan", "hazelnut", "pistachio", "macadamia"],
    "gluten": ["wheat", "bread", "pasta", "flour", "barley", "rye", "cereal", "cracker"],
    "soy": ["soy", "tofu", "tempeh", "edamame", "soybean"],
    "eggs": ["egg", "eggs", "omelet", "omelette"],
    "fish": ["fish", "salmon", "tuna", "cod", "halibut", "tilapia", "sardine"],
    "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel", "scallop"],
    "sesame": ["sesame", "tahini"],
    "mustard": ["mustard"],
    "celery": ["celery"],
    "sulfites": ["wine", "dried fruit"],
}

def expand_allergen_keywords(allergens: List[str]) -> List[str]:
    """
    Expand allergen list to include all related keywords
    
    Args:
        allergens: List of allergen categories or specific foods
    
    Returns:
        Expanded list of keywords to exclude
    """
    expanded = set()
    
    for allergen in allergens:
        allergen_lower = allergen.lower()
        
        # Check if it's a known category
        if allergen_lower in ALLERGEN_KEYWORDS:
            expanded.update(ALLERGEN_KEYWORDS[allergen_lower])
        else:
            # Add as-is if not a known category
            expanded.add(allergen_lower)
    
    return list(expanded)

async def substitute_food(
    original_food_name: str,
    allergens: List[str],
    nutrition_priority: str = "similar"  # 'similar', 'lower_calorie', 'higher_protein'
) -> Dict:
    """
    Find suitable food substitute for allergy
    
    Args:
        original_food_name: Name of food to substitute
        allergens: List of allergens to avoid
        nutrition_priority: What to prioritize in substitution
    
    Returns:
        Substitution recommendation with reasoning
    """
    # Search for original food
    original_foods = await search_foods_by_name(original_food_name, limit=1)
    
    if not original_foods:
        return {
            "found": False,
            "message": f"Original food '{original_food_name}' not found in database"
        }
    
    original = original_foods[0]
    
    # Expand allergen keywords
    exclude_keywords = expand_allergen_keywords(allergens)
    
    # Find similar foods excluding allergens
    alternatives = await find_similar_foods(
        protein=original['protein'] or 0,
        calories=original['calories'] or 0,
        exclude_keywords=exclude_keywords,
        limit=10
    )
    
    if not alternatives:
        return {
            "found": False,
            "original_food": original['description'],
            "message": "No suitable alternatives found that avoid specified allergens",
            "allergens_excluded": allergens
        }
    
    # Build prompt for AI recommendation
    prompt = build_allergy_substitution_prompt(
        original_food_name,
        allergens,
        alternatives
    )
    
    # Get AI recommendation
    ai_manager = get_ai_manager()
    response, api_used = await ai_manager.get_ai_response(prompt)
    
    return {
        "found": True,
        "original_food": {
            "description": original['description'],
            "calories": original['calories'],
            "protein": original['protein'],
            "sugar": original['sugar'],
            "sodium": original['sodium']
        },
        "alternatives_found": len(alternatives),
        "top_alternatives": [
            {
                "description": alt['description'],
                "portion": alt['portion_description'],
                "calories": alt['calories'],
                "protein": alt['protein'],
                "sugar": alt['sugar'],
                "similarity_score": alt.get('similarity_score', 0)
            }
            for alt in alternatives[:5]
        ],
        "ai_recommendation": response,
        "allergens_excluded": allergens,
        "api_used": api_used
    }

async def check_food_for_allergens(
    food_description: str,
    user_allergens: List[str]
) -> Dict:
    """
    Check if a food contains user's allergens
    
    Args:
        food_description: Food to check
        user_allergens: User's allergen list
    
    Returns:
        Safety assessment
    """
    # Expand allergen keywords
    allergen_keywords = expand_allergen_keywords(user_allergens)
    
    # Check if any allergen keyword appears in food description
    food_lower = food_description.lower()
    detected_allergens = []
    
    for allergen in allergen_keywords:
        if allergen in food_lower:
            detected_allergens.append(allergen)
    
    is_safe = len(detected_allergens) == 0
    
    return {
        "food": food_description,
        "is_safe": is_safe,
        "detected_allergens": detected_allergens,
        "user_allergens": user_allergens,
        "warning": None if is_safe else f"⚠️ Contains: {', '.join(detected_allergens)}"
    }

async def get_allergen_free_foods(
    category: str,
    allergens: List[str],
    limit: int = 20
) -> List[Dict]:
    """
    Get foods from a category that are free of specified allergens
    
    Args:
        category: Food category to search
        allergens: Allergens to exclude
        limit: Maximum results
    
    Returns:
        List of safe foods
    """
    from database.queries import get_foods_by_category
    
    exclude_keywords = expand_allergen_keywords(allergens)
    
    foods = await get_foods_by_category(
        categories=[category],
        exclude_keywords=exclude_keywords,
        limit_per_category=limit
    )
    
    # Double-check each food for safety
    safe_foods = []
    for food in foods:
        safety_check = await check_food_for_allergens(
            food['description'],
            allergens
        )
        
        if safety_check['is_safe']:
            safe_foods.append(food)
    
    return safe_foods

def get_common_substitutions() -> Dict:
    """
    Get common allergen substitutions reference
    """
    return {
        "dairy": {
            "milk": ["almond milk", "soy milk", "oat milk", "coconut milk"],
            "cheese": ["nutritional yeast", "cashew cheese", "tofu"],
            "yogurt": ["coconut yogurt", "almond yogurt", "soy yogurt"],
            "butter": ["coconut oil", "olive oil", "avocado", "vegan butter"]
        },
        "gluten": {
            "wheat_flour": ["rice flour", "almond flour", "coconut flour", "oat flour"],
            "bread": ["rice cakes", "corn tortillas", "gluten-free bread"],
            "pasta": ["rice noodles", "quinoa pasta", "zucchini noodles"]
        },
        "eggs": {
            "baking": ["flax egg", "chia egg", "applesauce", "mashed banana"],
            "breakfast": ["tofu scramble", "chickpea flour omelet"]
        },
        "nuts": {
            "snacks": ["seeds (sunflower, pumpkin)", "roasted chickpeas"],
            "nut_butter": ["sunflower seed butter", "soy nut butter"]
        }
    }
