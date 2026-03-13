"""
WHO Dietary Guidelines and Health Constants
Based on: WHO Fact Sheet - Healthy Diet (healthy-diet-fact-sheet-394.pdf)
"""

# WHO Dietary Guidelines (for adults, 2000 kcal/day reference)
WHO_GUIDELINES = {
    "FREE_SUGARS": {
        "recommended_max_g": 50,  # <10% of total energy
        "optimal_max_g": 25,       # <5% of total energy (additional health benefits)
        "recommended_max_pct": 10,
        "optimal_max_pct": 5,
        "daily_reference_kcal": 2000
    },
    "FRUITS_VEGETABLES": {
        "daily_min_g": 400,
        "portions_per_day": 5,
        "excludes": ["potatoes", "other starchy tubers"]
    },
    "FATS": {
        "total_fat_max_pct": 30,        # <30% of total energy
        "saturated_fat_max_pct": 10,    # <10% of total energy
        "trans_fat_max_pct": 1,         # <1% of total energy
        "trans_fat_goal": 0,            # Eliminate industrially-produced trans-fats
        "unsaturated_sources": ["fish", "nuts", "sunflower", "soybean", "canola", "olive oils"]
    },
    "SALT_SODIUM": {
        "salt_max_g": 5,           # <5g salt per day
        "sodium_max_mg": 2000,     # Equivalent to 2g sodium
        "recommendation": "Use iodized salt"
    },
    "POTASSIUM": {
        "daily_min_mg": 3510,      # Helps lower blood pressure
        "sources": ["fruits", "vegetables"]
    }
}

# BMI Classification (WHO Standards)
BMI_CATEGORIES = {
    "SEVERE_UNDERWEIGHT": {"max": 16.0, "label": "Severe Underweight", "color": "red"},
    "UNDERWEIGHT": {"min": 16.0, "max": 18.5, "label": "Underweight", "color": "yellow"},
    "NORMAL": {"min": 18.5, "max": 24.9, "label": "Normal (Healthy)", "color": "green"},
    "OVERWEIGHT": {"min": 25.0, "max": 29.9, "label": "Overweight", "color": "yellow"},
    "OBESE_CLASS_I": {"min": 30.0, "max": 34.9, "label": "Obese Class I", "color": "orange"},
    "OBESE_CLASS_II": {"min": 35.0, "max": 39.9, "label": "Obese Class II", "color": "orange"},
    "OBESE_CLASS_III": {"min": 40.0, "label": "Obese Class III", "color": "red"}
}

def get_bmi_category(bmi: float) -> dict:
    """Get BMI category and details based on WHO classification"""
    if bmi < 16.0:
        return BMI_CATEGORIES["SEVERE_UNDERWEIGHT"]
    elif bmi < 18.5:
        return BMI_CATEGORIES["UNDERWEIGHT"]
    elif bmi < 25.0:
        return BMI_CATEGORIES["NORMAL"]
    elif bmi < 30.0:
        return BMI_CATEGORIES["OVERWEIGHT"]
    elif bmi < 35.0:
        return BMI_CATEGORIES["OBESE_CLASS_I"]
    elif bmi < 40.0:
        return BMI_CATEGORIES["OBESE_CLASS_II"]
    else:
        return BMI_CATEGORIES["OBESE_CLASS_III"]

# Sugar Level Warnings
SUGAR_WARNING_LEVELS = {
    "SAFE": {"max": 25, "label": "Safe", "message": "Within optimal WHO guidelines (<5% energy)."},
    "MODERATE": {"min": 25, "max": 50, "label": "Moderate", "message": "Between optimal and maximum WHO limits. Consider reducing sugar intake."},
    "HIGH": {"min": 50, "label": "High", "message": "⚠️ Exceeds WHO daily limit (50g). High risk for obesity, dental caries, and NCDs."}
}

def get_sugar_warning_level(sugar_g: float) -> dict:
    """Get warning level for sugar consumption"""
    if sugar_g < 25:
        return SUGAR_WARNING_LEVELS["SAFE"]
    elif sugar_g < 50:
        return SUGAR_WARNING_LEVELS["MODERATE"]
    else:
        return SUGAR_WARNING_LEVELS["HIGH"]

# Sodium Warning Levels
SODIUM_WARNING_LEVELS = {
    "SAFE": {"max": 1500, "label": "Safe", "message": "Well within WHO guidelines."},
    "MODERATE": {"min": 1500, "max": 2000, "label": "Moderate", "message": "Approaching WHO daily limit. Monitor salt intake."},
    "HIGH": {"min": 2000, "label": "High", "message": "⚠️ Exceeds WHO daily sodium limit (2000mg). May increase blood pressure and cardiovascular risk."}
}

def get_sodium_warning_level(sodium_mg: float) -> dict:
    """Get warning level for sodium consumption"""
    if sodium_mg < 1500:
        return SODIUM_WARNING_LEVELS["SAFE"]
    elif sodium_mg < 2000:
        return SODIUM_WARNING_LEVELS["MODERATE"]
    else:
        return SODIUM_WARNING_LEVELS["HIGH"]

# Activity Level Multipliers (for calorie calculation)
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,      # Little or no exercise
    "light": 1.375,        # Light exercise 1-3 days/week
    "moderate": 1.55,      # Moderate exercise 3-5 days/week
    "active": 1.725,       # Hard exercise 6-7 days/week
    "very_active": 1.9     # Very hard exercise, physical job
}

# Calorie Adjustments for Weight Goals
CALORIE_ADJUSTMENTS = {
    "lose": -500,          # 500 kcal deficit for weight loss (~0.5kg/week)
    "lose_fast": -750,     # 750 kcal deficit for faster loss (~0.75kg/week)
    "maintain": 0,         # No adjustment
    "gain": 300,           # 300 kcal surplus for lean muscle gain
    "gain_bulk": 500       # 500 kcal surplus for faster weight gain
}
