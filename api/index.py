"""
Vercel serverless function handler for FastAPI
"""
from app.main import app

# This is required for Vercel to properly route requests
handler = app
