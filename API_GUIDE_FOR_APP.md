# Health Chatbot API - App Integration Guide

**Base URL:** `https://health-chatbot-api-fo9t.onrender.com`  
**API Docs:** `https://health-chatbot-api-fo9t.onrender.com/docs`

---

## 🔑 Authentication
The API uses **session-based authentication**. Create a session first, then use the `session_id` in all subsequent requests.

---

## 📋 Core Endpoints

### 1️⃣ **Session Management**

#### Create Session
```http
POST /api/session
```
**Response:**
```json
{
  "session_id": "uuid",
  "created_at": "2026-03-13T09:21:33",
  "expires_at": "2026-03-20T09:21:33"
}
```
**Usage:** Call this when user opens the app. Session lasts 7 days.

---

### 2️⃣ **BMI & Calorie Calculator**

#### Calculate BMI
```http
POST /api/bmi
```
**Request:**
```json
{
  "session_id": "uuid",
  "age": 25,
  "height_cm": 170,
  "weight_kg": 70,
  "gender": "male",
  "activity_level": "moderate",
  "goal": "maintain"
}
```

**Activity Levels:** `sedentary` | `light` | `moderate` | `active` | `very_active`  
**Goals:** `lose` | `lose_fast` | `maintain` | `gain` | `gain_bulk`

**Response:**
```json
{
  "bmi": 24.22,
  "category": "Normal (Healthy)",
  "color": "green",
  "bmr": 1731,
  "tdee": 2425,
  "target_calories": 2546,
  "goal": "maintain",
  "macros": {
    "protein_g": 127,
    "carbs_g": 318,
    "fat_g": 71
  },
  "recommendations": {
    "min_calories": 2037,
    "max_calories": 3056
  }
}
```

---

### 3️⃣ **AI Health Chatbot** (RAG-Powered)

#### Ask Health Question
```http
POST /api/query
```
**Request:**
```json
{
  "session_id": "uuid",
  "query": "What are the health benefits of almonds?"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "query": "What are the health benefits of almonds?",
  "response_text": "Almonds offer a variety of health benefits...",
  "query_type": "food_nutrition",
  "matched_foods_count": 5,
  "api_used": "gemini"
}
```

**What it does:**
- Uses RAG (Retrieval-Augmented Generation) to search 22,043 foods in database
- Provides WHO guideline-compliant health advice
- Remembers conversation history from session
- Considers user's BMI, allergies, and preferences

---

### 4️⃣ **Food Database Search**

#### Search Foods
```http
GET /api/food/search?q=chicken&limit=10
```

**Response:**
```json
{
  "query": "chicken",
  "count": 5,
  "foods": [
    {
      "name": "Chicken breast, grilled",
      "calories": 165,
      "protein": 31.0,
      "carbs": 0.0,
      "fat": 3.6,
      "sugar": 0.0,
      "sodium": 74.0,
      "fiber": 0.0
    }
  ]
}
```

---

### 5️⃣ **Diet Plan Generator**

#### Generate Meal Plan
```http
POST /api/diet-plan
```
**Request:**
```json
{
  "session_id": "uuid",
  "goal": "lose",
  "allergies": ["peanuts", "shellfish"],
  "preferences": ["vegetarian", "low-carb"]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "goal": "lose",
  "target_calories": 1800,
  "meal_plan": "Detailed personalized meal plan...",
  "foods_considered": 150,
  "excluded_allergens": ["peanuts", "shellfish"],
  "api_used": "gemini"
}
```

**Note:** User must calculate BMI first (POST /api/bmi) before generating meal plan.

---

### 6️⃣ **Allergy Management**

#### Get Food Substitution
```http
POST /api/allergy/substitute
```
**Request:**
```json
{
  "session_id": "uuid",
  "original_food": "peanut butter",
  "allergens": ["peanuts"]
}
```

**Response:**
```json
{
  "found": true,
  "original_food": { "name": "Peanut butter", "calories": 588 },
  "alternatives_found": 5,
  "top_alternatives": [
    { "name": "Almond butter", "calories": 614, "match_score": 0.95 }
  ],
  "ai_recommendation": "Detailed AI explanation...",
  "allergens_excluded": ["peanuts"],
  "api_used": "gemini"
}
```

#### Update User Allergies
```http
PUT /api/session/allergies
```
**Request:**
```json
{
  "session_id": "uuid",
  "allergies": ["peanuts", "shellfish", "dairy"]
}
```

#### Update Dietary Preferences
```http
PUT /api/session/preferences
```
**Request:**
```json
{
  "session_id": "uuid",
  "preferences": ["vegetarian", "gluten-free", "low-sugar"]
}
```

---

### 7️⃣ **Daily Nutrition Tracking**

#### Get Today's Intake
```http
GET /api/daily-intake/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid",
  "date": "2026-03-13",
  "total_calories": 1850,
  "total_sugar": 32.5,
  "total_sodium": 1800,
  "meals_count": 3,
  "who_status": {
    "sugar": {
      "consumed": 32.5,
      "daily_max": 50,
      "daily_optimal": 25,
      "percentage_of_max": 65.0,
      "status": "warning"
    },
    "sodium": {
      "consumed": 1800,
      "daily_max": 2000,
      "percentage_of_max": 90.0,
      "status": "safe"
    }
  },
  "warnings": ["Sugar intake approaching daily limit"]
}
```

#### Log Food Intake
```http
POST /api/daily-intake/log
```
**Request:**
```json
{
  "session_id": "uuid",
  "food_description": "500ml Coca-Cola",
  "quantity": 500,
  "unit": "ml"
}
```

---

### 8️⃣ **Health Check**

#### System Status
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": {
    "total_rows": 22043,
    "unique_foods": 5394,
    "status": "connected"
  },
  "ai_clients": {
    "gemini": { "available": true },
    "xai-grok": { "available": true }
  }
}
```

---

## 🎨 UI Design Considerations

### Recommended Screens:
1. **Onboarding:** Collect age, height, weight, gender, activity level, goal
2. **Chat Interface:** Main screen for asking health questions
3. **BMI Dashboard:** Display BMI, category, calorie target, macros
4. **Food Search:** Search bar + nutrition cards
5. **Meal Planner:** Show personalized meal plans
6. **Daily Tracker:** Progress bars for calories, sugar, sodium vs WHO limits
7. **Profile Settings:** Manage allergies and dietary preferences

### Key Features to Highlight:
- **AI-Powered Answers:** Gemini + Grok fallback (always available)
- **22,043 Foods Database:** Comprehensive nutrition data
- **WHO Guidelines Compliance:** Shows if user exceeds sugar/sodium limits
- **Personalized:** Remembers BMI, allergies, preferences
- **Session Persistence:** 7-day sessions, no login required

---

## 🔒 Rate Limits
- Chatbot queries: **20/minute**
- Food search: **30/minute**
- BMI calculation: **20/minute**
- Session creation: **10/minute**

---

## ⚡ Performance
- **Average response time:** 1-3 seconds (AI responses)
- **Database queries:** < 100ms
- **Uptime:** 24/7 on Render free tier (may sleep after 15min inactivity)

---

## 🚀 Quick Start Example

```javascript
// 1. Create session
const session = await fetch('https://health-chatbot-api-fo9t.onrender.com/api/session', {
  method: 'POST'
}).then(r => r.json());

// 2. Calculate BMI
const bmi = await fetch('https://health-chatbot-api-fo9t.onrender.com/api/bmi', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session.session_id,
    age: 25,
    height_cm: 170,
    weight_kg: 70,
    gender: 'male',
    activity_level: 'moderate',
    goal: 'maintain'
  })
}).then(r => r.json());

// 3. Ask health question
const answer = await fetch('https://health-chatbot-api-fo9t.onrender.com/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session.session_id,
    query: 'What should I eat for breakfast?'
  })
}).then(r => r.json());

console.log(answer.response_text);
```

---

**Need more details?** Visit interactive docs at `/docs` endpoint.
