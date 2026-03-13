"""
AI Client Manager with Smart Failover
Gemini (primary) → Grok/xAI (fallback)
"""

import os
import time
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AI SDKs
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")

try:
    import httpx
    XAI_AVAILABLE = True
except ImportError:
    XAI_AVAILABLE = False
    print("⚠️  httpx not installed. Install with: pip install httpx")

class AIClientManager:
    """
    Manages AI API clients with automatic failover
    Tries Gemini first, falls back to Grok on errors
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.xai_api_key = os.getenv("XAI_API_KEY")
        
        self.gemini_client = None
        self.xai_client = None
        
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AI clients"""
        
        # Initialize Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Use Gemini 2.5 Flash Lite - fast and cost-effective
                self.gemini_client = genai.GenerativeModel('gemini-2.5-flash-lite')
                print("✅ Gemini API initialized (gemini-2.5-flash-lite)")
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
        else:
            print("⚠️  Gemini API key not found in .env")
        
        # Initialize xAI Grok
        if XAI_AVAILABLE and self.xai_api_key:
            try:
                self.xai_client = httpx.AsyncClient()
                print("✅ xAI Grok API initialized (grok-4-1-fast-non-reasoning)")
            except Exception as e:
                print(f"⚠️  xAI initialization failed: {e}")
        else:
            print("⚠️  xAI API key not found in .env")
        
        if not self.gemini_client and not self.xai_client:
            raise ValueError(
                "No AI API configured. Please set GEMINI_API_KEY or XAI_API_KEY in .env"
            )
    
    async def _call_gemini(self, prompt: str, max_retries: int = 2) -> str:
        """Call Gemini API with retry logic"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized")
        
        for attempt in range(max_retries):
            try:
                response = self.gemini_client.generate_content(prompt)
                return response.text
            
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limit (429)
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"⚠️  Gemini rate limit hit (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise
                
                # Other errors
                print(f"⚠️  Gemini error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise
        
        raise Exception("Gemini: Max retries exceeded")
    
    async def _call_xai(self, prompt: str, max_retries: int = 2) -> str:
        """Call xAI Grok API with retry logic"""
        if not self.xai_client:
            raise ValueError("xAI client not initialized")
        
        for attempt in range(max_retries):
            try:
                response = await self.xai_client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.xai_api_key}"
                    },
                    json={
                        "messages": [
                            {"role": "system", "content": "You are a knowledgeable health and nutrition assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "model": "grok-4-1-fast-non-reasoning",  # Fast, cheap, good quality
                        "stream": False,
                        "temperature": 0.7,
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']
            
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  xAI Grok error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        
        raise Exception("xAI Grok: Max retries exceeded")
    
    async def get_ai_response(
        self,
        prompt: str,
        prefer_gemini: bool = True
    ) -> Tuple[str, str]:
        """
        Get AI response with smart failover
        
        Returns:
            Tuple[response_text, api_used]
        """
        start_time = time.time()
        
        # Try Gemini first (if preferred and available)
        if prefer_gemini and self.gemini_client:
            try:
                response = await self._call_gemini(prompt)
                elapsed = time.time() - start_time
                print(f"✅ Gemini response received ({elapsed:.2f}s)")
                return response, "gemini"
            
            except Exception as e:
                print(f"❌ Gemini failed: {e}")
                print("🔄 Switching to xAI Grok...")
        
        # Fallback to xAI Grok
        if self.xai_client:
            try:
                response = await self._call_xai(prompt)
                elapsed = time.time() - start_time
                print(f"✅ xAI Grok response received ({elapsed:.2f}s)")
                return response, "xai-grok"
            
            except Exception as e:
                print(f"❌ xAI Grok also failed: {e}")
                raise Exception("Both Gemini and xAI Grok APIs failed")
        
        raise Exception("No AI API available for response")
    
    def get_status(self) -> Dict:
        """Get status of AI clients"""
        return {
            "gemini": {
                "available": self.gemini_client is not None,
                "api_key_set": bool(self.gemini_api_key)
            },
            "xai-grok": {
                "available": self.xai_client is not None,
                "api_key_set": bool(self.xai_api_key)
            }
        }
    
    async def close(self):
        """Cleanup resources"""
        if self.xai_client:
            await self.xai_client.aclose()

# Global AI manager instance
ai_manager = None

def get_ai_manager() -> AIClientManager:
    """Get or create AI manager instance"""
    global ai_manager
    if ai_manager is None:
        ai_manager = AIClientManager()
    return ai_manager
