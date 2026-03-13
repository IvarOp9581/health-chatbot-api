"""
Nutrition Analysis Service
Food lookup, portion scaling, sugar/sodium warnings
"""

from typing import Dict, List, Optional
from database.queries import search_foods_by_name, get_food_by_id
from database.guidelines import get_sugar_warning_level, get_sodium_warning_level

async def analyze_food_intake(
    food_description: str,
    quantity: float = 1.0,
    unit: Optional[str] = None
) -> Dict:
    """
    Analyze nutritional content of food intake
    
    Args:
        food_description: Name/description of food
        quantity: Amount consumed
        unit: Unit of measurement (if applicable)
    
    Returns:
        Nutritional analysis with warnings
    """
    # Search for matching foods
    foods = await search_foods_by_name(food_description, limit=5)
    
    if not foods:
        return {
            "found": False,
            "message": f"Food '{food_description}' not found in database",
            "suggestions": "Try searching with different keywords"
        }
    
    # Use first match (most relevant)
    food = foods[0]
    
    # Calculate scaled nutrition based on quantity and portion
    # Database values are stored PER PORTION (gram_weight)
    # User specifies quantity in grams (or other units)
    gram_weight = food['gram_weight'] or 100  # Default to 100g if not specified
    
    # Determine scale factor based on unit
    if unit and unit.lower() in ['g', 'gram', 'grams']:
        # User specified grams, so scale based on gram weight
        scale_factor = quantity / gram_weight
    elif unit and unit.lower() in ['cup', 'cups']:
        # User specified cups - treat as number of portions
        scale_factor = quantity
    else:
        # No unit or other unit - treat quantity as number of portions
        scale_factor = quantity
    
    total_calories = (food['calories'] or 0) * scale_factor
    total_sugar = (food['sugar'] or 0) * scale_factor
    total_protein = (food['protein'] or 0) * scale_factor
    total_sodium = (food['sodium'] or 0) * scale_factor
    
    # Get warnings
    sugar_warning = get_sugar_warning_level(total_sugar)
    sodium_warning = get_sodium_warning_level(total_sodium)
    
    return {
        "found": True,
        "food": {
            "description": food['description'],
            "portion": food['portion_description'],
            "quantity_consumed": quantity,
            "gram_weight": gram_weight * quantity
        },
        "nutrition": {
            "calories": round(total_calories, 1),
            "sugar_g": round(total_sugar, 1),
            "protein_g": round(total_protein, 1),
            "sodium_mg": round(total_sodium, 1)
        },
        "warnings": {
            "sugar": {
                "level": sugar_warning['label'],
                "message": sugar_warning['message']
            },
            "sodium": {
                "level": sodium_warning['label'],
                "message": sodium_warning['message']
            }
        },
        "who_comparison": {
            "sugar_percent_of_daily_limit": round((total_sugar / 50) * 100, 1),
            "sodium_percent_of_daily_limit": round((total_sodium / 2000) * 100, 1)
        },
        "alternative_matches": [
            {
                "description": f['description'],
                "portion": f['portion_description'],
                "calories": f['calories'],
                "sugar": f['sugar']
            }
            for f in foods[1:4]  # Show 3 alternatives
        ]
    }

async def calculate_meal_nutrition(food_items: List[Dict]) -> Dict:
    """
    Calculate total nutrition for a meal with multiple foods
    
    Args:
        food_items: List of {food_description, quantity, unit}
    
    Returns:
        Aggregated nutritional data
    """
    total_calories = 0
    total_sugar = 0
    total_protein = 0
    total_sodium = 0
    analyzed_items = []
    
    for item in food_items:
        analysis = await analyze_food_intake(
            item['food_description'],
            item.get('quantity', 1.0),
            item.get('unit')
        )
        
        if analysis['found']:
            nutrition = analysis['nutrition']
            total_calories += nutrition['calories']
            total_sugar += nutrition['sugar_g']
            total_protein += nutrition['protein_g']
            total_sodium += nutrition['sodium_mg']
            
            analyzed_items.append({
                "food": analysis['food']['description'],
                "nutrition": nutrition
            })
    
    # Overall warnings
    sugar_warning = get_sugar_warning_level(total_sugar)
    sodium_warning = get_sodium_warning_level(total_sodium)
    
    return {
        "items": analyzed_items,
        "totals": {
            "calories": round(total_calories, 1),
            "sugar_g": round(total_sugar, 1),
            "protein_g": round(total_protein, 1),
            "sodium_mg": round(total_sodium, 1)
        },
        "warnings": {
            "sugar": sugar_warning,
            "sodium": sodium_warning
        },
        "who_comparison": {
            "sugar_percent": round((total_sugar / 50) * 100, 1),
            "sodium_percent": round((total_sodium / 2000) * 100, 1)
        }
    }

async def find_healthier_alternatives(
    food_description: str,
    prefer_lower: str = "sugar",  # 'sugar', 'calories', 'sodium'
    limit: int = 5
) -> List[Dict]:
    """
    Find healthier alternatives to a food item
    """
    # Get original food
    foods = await search_foods_by_name(food_description, limit=1)
    
    if not foods:
        return []
    
    original = foods[0]
    original_value = original.get(prefer_lower, 0)
    
    # Search for similar foods
    all_foods = await search_foods_by_name(food_description, limit=20)
    
    # Filter for healthier options
    healthier = []
    for food in all_foods:
        current_value = food.get(prefer_lower, 0)
        
        # Must be lower in target nutrient
        if current_value < original_value:
            reduction = ((original_value - current_value) / original_value) * 100
            healthier.append({
                "description": food['description'],
                "portion": food['portion_description'],
                "calories": food['calories'],
                "sugar": food['sugar'],
                "sodium": food['sodium'],
                "reduction": round(reduction, 1),
                "reduction_metric": prefer_lower
            })
    
    # Sort by reduction percentage
    healthier.sort(key=lambda x: x['reduction'], reverse=True)
    
    return healthier[:limit]
