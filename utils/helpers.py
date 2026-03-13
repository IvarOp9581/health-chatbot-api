"""
Utility Helper Functions
"""

import re
from typing import List, Dict

def extract_quantity_from_query(query: str) -> tuple:
    """
    Extract quantity and unit from user query
    
    Examples:
        "I drank 500ml coke" -> (500, 'ml', 'coke')
        "I had 2 cups of rice" -> (2, 'cups', 'rice')
    
    Returns:
        (quantity, unit, remaining_text)
    """
    # Pattern: number + optional unit
    pattern = r'(\d+\.?\d*)\s*(ml|l|g|kg|oz|cup|cups|glass|glasses|can|cans|bottle|bottles|piece|pieces)?'
    
    matches = re.findall(pattern, query.lower())
    
    if matches:
        quantity_str, unit = matches[0]
        quantity = float(quantity_str)
        
        # Remove quantity and unit from query
        cleaned_query = re.sub(pattern, '', query, count=1).strip()
        
        return quantity, unit if unit else None, cleaned_query
    
    return 1.0, None, query

def format_calories(calories: float) -> str:
    """Format calories for display"""
    return f"{calories:,.0f} kcal"

def format_macros(protein: float, carbs: float, fat: float) -> str:
    """Format macros for display"""
    return f"P: {protein:.1f}g | C: {carbs:.1f}g | F: {fat:.1f}g"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_food_list_from_text(text: str) -> List[str]:
    """
    Parse list of foods from comma/and-separated text
    
    Example:
        "apple, banana and orange" -> ['apple', 'banana', 'orange']
    """
    # Replace 'and' with comma
    text = text.replace(' and ', ', ')
    
    # Split by comma
    foods = [f.strip() for f in text.split(',')]
    
    return [f for f in foods if f]

def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage safely"""
    if total == 0:
        return 0.0
    return (part / total) * 100

def normalize_allergen_name(allergen: str) -> str:
    """Normalize allergen name for consistency"""
    allergen_map = {
        'dairy': ['milk', 'dairy', 'lactose'],
        'gluten': ['gluten', 'wheat'],
        'nuts': ['nuts', 'tree nuts', 'peanuts'],
        'eggs': ['egg', 'eggs'],
        'fish': ['fish'],
        'shellfish': ['shellfish', 'seafood'],
        'soy': ['soy', 'soya']
    }
    
    allergen_lower = allergen.lower().strip()
    
    for standard, variants in allergen_map.items():
        if allergen_lower in variants:
            return standard
    
    return allergen_lower

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove potentially dangerous characters for SQL (though we use parameterized queries)
    # This is defense in depth
    text = text.replace(';', '').replace('--', '')
    
    return text.strip()
