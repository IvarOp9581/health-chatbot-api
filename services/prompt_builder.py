"""
Prompt Builder for RAG
Context-aware prompt templates for different query types
"""

from typing import Dict, List

def format_food_list(foods: List[Dict], max_items: int = 10) -> str:
    """Format food list for prompt"""
    if not foods:
        return "No matching foods found in database."
    
    formatted = []
    for food in foods[:max_items]:
        formatted.append(
            f"- {food['description']} ({food['portion_description']}): "
            f"{food['calories']} kcal, {food['sugar']}g sugar, "
            f"{food['protein']}g protein, {food['sodium']}mg sodium"
        )
    
    return "\n".join(formatted)

def build_sugar_analysis_prompt(query: str, context: Dict) -> str:
    """
    Build prompt for sugar/nutrition analysis
    """
    foods_str = format_food_list(context['matched_foods'])
    who_guidelines = context['who_guidelines']
    
    prompt = f"""You are a health and nutrition expert. Analyze the user's food intake and provide warnings based on WHO guidelines.

USER QUERY: {query}

MATCHED FOODS FROM DATABASE:
{foods_str}

WHO SUGAR GUIDELINES:
- Maximum: {who_guidelines['free_sugars']['recommended_max_g']}g/day (10% of 2000 kcal)
- Optimal: {who_guidelines['free_sugars']['optimal_max_g']}g/day (5% of 2000 kcal)
- Exceeding these limits increases risk of obesity, dental caries, and NCDs

TASK:
1. Identify which food(s) the user consumed from the database
2. Calculate total sugar, calories, and sodium
3. Compare against WHO guidelines
4. Provide clear health warning if limits exceeded
5. Suggest healthier alternatives if needed

Be specific, cite the exact nutritional values from the database, and be direct about health risks."""
    
    return prompt

def build_diet_plan_prompt(goal: str, context: Dict) -> str:
    """
    Build prompt for personalized diet plan generation
    """
    user_data = context['user_context']
    bmi_data = user_data.get('bmi_data', {})
    allergies = user_data.get('allergies', [])
    foods_str = format_food_list(context['matched_foods'], max_items=50)
    who_guidelines = context['who_guidelines']
    
    allergy_str = ", ".join(allergies) if allergies else "None"
    
    prompt = f"""You are a professional nutritionist. Create a personalized meal plan based on WHO guidelines and user data.

USER PROFILE:
- BMI: {bmi_data.get('bmi', 'Not provided')} ({bmi_data.get('category', 'Unknown')})
- Daily Calorie Target: {bmi_data.get('daily_calories', 'Not calculated')} kcal
- Goal: {goal.upper()} weight
- Allergies: {allergy_str}

AVAILABLE FOODS FROM DATABASE (use ONLY these):
{foods_str}

WHO DIETARY GUIDELINES:
- Fruits/Vegetables: {who_guidelines['fruits_vegetables']['daily_min_g']}g daily ({who_guidelines['fruits_vegetables']['portions_per_day']} portions)
- Sugar: <{who_guidelines['free_sugars']['recommended_max_g']}g/day (ideally <{who_guidelines['free_sugars']['optimal_max_g']}g)
- Salt: <{who_guidelines['salt_sodium']['salt_max_g']}g/day
- Total Fat: <30% of energy, Saturated Fat: <10%, Trans Fat: <1%

TASK:
Create a complete 3-meal plan (Breakfast, Lunch, Dinner) that:
1. Uses ONLY foods from the database list above
2. Matches user's calorie target (±100 kcal)
3. Excludes ALL allergens
4. Follows WHO guidelines
5. Includes diverse food groups

FORMAT:
**BREAKFAST:**
- Food 1 (portion): calories, macros
- Food 2 (portion): calories, macros
Subtotal: X kcal, Xg protein, Xg sugar

**LUNCH:** (same format)

**DINNER:** (same format)

**DAILY TOTALS:** X kcal, Xg protein, Xg sugar, Xmg sodium

Be specific with portions and verify all foods are from the database."""
    
    return prompt

def build_allergy_substitution_prompt(original_food: str, allergens: List[str], alternatives: List[Dict]) -> str:
    """
    Build prompt for food substitution due to allergies
    """
    allergens_str = ", ".join(allergens)
    alternatives_str = format_food_list(alternatives, max_items=10)
    
    prompt = f"""You are a nutrition expert helping with food allergies. Suggest the best substitution.

USER REQUEST: Substitute for "{original_food}"
ALLERGIES: {allergens_str}

ALTERNATIVE FOODS FROM DATABASE (allergy-safe):
{alternatives_str}

TASK:
1. Select the BEST alternative from the list above
2. Explain why it's a good substitute (similar nutrition/taste/use)
3. Provide nutritional comparison
4. Suggest how to use it

Be concise and practical."""
    
    return prompt

def build_bmi_consultation_prompt(bmi_data: Dict, query: str) -> str:
    """
    Build prompt for BMI-related questions
    """
    prompt = f"""You are a health consultant. Provide BMI guidance based on WHO standards.

USER BMI DATA:
- BMI: {bmi_data.get('bmi', 'Not calculated')}
- Category: {bmi_data.get('category', 'Unknown')}
- Daily Calorie Needs: {bmi_data.get('daily_calories', 'Not calculated')} kcal

USER QUESTION: {query}

WHO BMI CATEGORIES:
- Underweight: <18.5
- Normal: 18.5-24.9
- Overweight: 25-29.9
- Obese: ≥30

TASK:
1. Interpret the user's BMI category
2. Answer their specific question
3. Provide actionable health advice
4. Recommend calorie adjustment if needed for their goal
5. Note: Always recommend consulting healthcare provider for medical advice

Be supportive and evidence-based."""
    
    return prompt

def build_general_health_prompt(query: str, context: Dict) -> str:
    """
    Build prompt for general health queries
    """
    foods_str = format_food_list(context['matched_foods'])
    
    prompt = f"""You are a knowledgeable health and nutrition assistant. Answer the user's health question accurately.

USER QUESTION: {query}

RELEVANT FOODS FROM DATABASE:
{foods_str}

WHO HEALTH GUIDELINES:
- Eat 400g+ fruits/vegetables daily
- Limit sugar to <50g/day (ideally <25g)
- Limit salt to <5g/day
- Get diverse nutrients from varied diet
- Balance energy intake with physical activity

TASK:
Provide a helpful, accurate answer using:
1. Database nutritional information (if relevant)
2. WHO guidelines
3. Evidence-based health advice

Be clear, concise, and cite specific data when available."""
    
    return prompt

async def build_prompt(query: str, context: Dict) -> str:
    """
    Main prompt builder - routes to specific template based on query type
    """
    query_type = context['query_type']
    
    if query_type == 'sugar_check':
        return build_sugar_analysis_prompt(query, context)
    
    elif query_type == 'diet_plan':
        goal = context['user_context'].get('goal', 'maintain')
        return build_diet_plan_prompt(goal, context)
    
    elif query_type == 'allergy':
        # This requires additional parameters, handle in endpoint
        return build_general_health_prompt(query, context)
    
    elif query_type == 'bmi':
        bmi_data = context['user_context'].get('bmi_data', {})
        return build_bmi_consultation_prompt(bmi_data, query)
    
    else:
        return build_general_health_prompt(query, context)
