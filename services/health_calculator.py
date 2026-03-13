"""
Health Calculator Service
BMI calculation and daily calorie needs (Mifflin-St Jeor equation)
"""

from typing import Dict
from database.guidelines import get_bmi_category, ACTIVITY_MULTIPLIERS, CALORIE_ADJUSTMENTS

def calculate_bmi(weight_kg: float, height_cm: float) -> Dict:
    """
    Calculate BMI from weight and height
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
    
    Returns:
        Dict with BMI value, category, and WHO classification
    """
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    bmi_category = get_bmi_category(bmi)
    
    return {
        "bmi": round(bmi, 2),
        "category": bmi_category["label"],
        "color": bmi_category["color"],
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "height_m": round(height_m, 2)
    }

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
    
    Men: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(y) + 5
    Women: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(y) - 161
    """
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    
    if gender.lower() in ['male', 'm', 'man']:
        bmr += 5
    elif gender.lower() in ['female', 'f', 'woman']:
        bmr -= 161
    else:
        # Default to average if gender not specified
        bmr -= 78  # Average of +5 and -161
    
    return bmr

def calculate_tdee(bmr: float, activity_level: str = "moderate") -> float:
    """
    Calculate Total Daily Energy Expenditure
    
    Args:
        bmr: Basal Metabolic Rate
        activity_level: sedentary, light, moderate, active, very_active
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)
    return bmr * multiplier

def calculate_calorie_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate",
    goal: str = "maintain"
) -> Dict:
    """
    Calculate personalized daily calorie target
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: 'male' or 'female'
        activity_level: Activity level (sedentary to very_active)
        goal: 'lose', 'lose_fast', 'maintain', 'gain', 'gain_bulk'
    
    Returns:
        Dict with BMR, TDEE, target calories, and recommendations
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    
    # Adjust for goal
    adjustment = CALORIE_ADJUSTMENTS.get(goal.lower(), 0)
    target_calories = tdee + adjustment
    
    # Calculate macros (general guidelines)
    protein_g = weight_kg * 1.6 if goal in ['gain', 'gain_bulk'] else weight_kg * 1.2
    fat_g = target_calories * 0.25 / 9  # 25% of calories from fat
    carbs_g = (target_calories - (protein_g * 4 + fat_g * 9)) / 4
    
    return {
        "bmr": round(bmr, 0),
        "tdee": round(tdee, 0),
        "target_calories": round(target_calories, 0),
        "adjustment": adjustment,
        "goal": goal,
        "activity_level": activity_level,
        "macros": {
            "protein_g": round(protein_g, 1),
            "fat_g": round(fat_g, 1),
            "carbs_g": round(carbs_g, 1)
        },
        "recommendations": get_calorie_recommendations(goal, adjustment)
    }

def get_calorie_recommendations(goal: str, adjustment: int) -> Dict:
    """Get recommendations based on calorie goal"""
    recommendations = {
        "lose": {
            "message": f"Creating {abs(adjustment)} kcal deficit for gradual weight loss (~0.5kg/week)",
            "tips": [
                "Focus on high-protein foods to preserve muscle",
                "Eat plenty of vegetables for satiety",
                "Stay hydrated",
                "Combine with regular exercise"
            ]
        },
        "lose_fast": {
            "message": f"Creating {abs(adjustment)} kcal deficit for faster weight loss (~0.75kg/week)",
            "tips": [
                "Ensure adequate protein intake",
                "Monitor energy levels",
                "Consider a multivitamin",
                "Consult healthcare provider if extending beyond 12 weeks"
            ]
        },
        "maintain": {
            "message": "Maintaining current weight with balanced energy intake",
            "tips": [
                "Focus on nutrient-dense foods",
                "Stay active",
                "Monitor weight weekly",
                "Adjust if weight trends up/down"
            ]
        },
        "gain": {
            "message": f"Creating {adjustment} kcal surplus for lean muscle gain",
            "tips": [
                "Increase protein to 1.6-2.2g per kg bodyweight",
                "Combine with resistance training",
                "Focus on whole foods",
                "Gain 0.25-0.5kg per week maximum"
            ]
        },
        "gain_bulk": {
            "message": f"Creating {adjustment} kcal surplus for faster weight gain",
            "tips": [
                "Ensure high protein intake",
                "Train regularly with progressive overload",
                "Some fat gain is expected",
                "Monitor progress weekly"
            ]
        }
    }
    
    return recommendations.get(goal, recommendations["maintain"])

def calculate_full_health_profile(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate",
    goal: str = "maintain"
) -> Dict:
    """
    Calculate complete health profile including BMI and calorie needs
    """
    bmi_data = calculate_bmi(weight_kg, height_cm)
    calorie_data = calculate_calorie_target(
        weight_kg, height_cm, age, gender, activity_level, goal
    )
    
    return {
        **bmi_data,
        **calorie_data,
        "age": age,
        "gender": gender
    }
