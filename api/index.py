"""
Vercel serverless function handler for FastAPI
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set Vercel flag
os.environ['VERCEL'] = '1'

# Import FastAPI app
try:
    from app.main import app
    print("✅ Successfully imported FastAPI app")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export for Vercel
handler = app
