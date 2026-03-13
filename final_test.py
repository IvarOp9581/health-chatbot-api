#!/usr/bin/env python3
"""
Final Production Test - Quick validation before deployment
"""
import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

async def test_production_ready():
    """Run essential production checks"""
    print("🚀 FINAL PRODUCTION TEST")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Health Check
        print("\n1️⃣  Testing Health Check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data['status']}")
                print(f"   ✅ Database: {data['database']['status']}")
                print(f"   ✅ AI: {data['ai']['gemini']['status']}")
                tests_passed += 1
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            tests_failed += 1
        
        # Test 2: Session Creation
        print("\n2️⃣  Testing Session Creation...")
        try:
            response = await client.post(f"{BASE_URL}/sessions/create", json={})
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                print(f"   ✅ Session created: {session_id}")
                tests_passed += 1
            else:
                print(f"   ❌ Session creation failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            tests_failed += 1
        
        # Test 3: Food Search
        print("\n3️⃣  Testing Food Search...")
        try:
            response = await client.get(f"{BASE_URL}/nutrition/search?query=chicken")
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Found {len(results)} results")
                if results:
                    print(f"   ✅ Sample: {results[0]['food_name']}")
                tests_passed += 1
            else:
                print(f"   ❌ Food search failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            tests_failed += 1
        
        # Test 4: AI Chat
        print("\n4️⃣  Testing AI Chat...")
        try:
            response = await client.post(f"{BASE_URL}/chat", json={
                "session_id": session_id,
                "message": "What's a healthy breakfast?"
            })
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                print(f"   ✅ AI responded: {response_text[:100]}...")
                tests_passed += 1
            else:
                print(f"   ❌ AI chat failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {tests_passed} passed, {tests_failed} failed")
    total = tests_passed + tests_failed
    percentage = (tests_passed / total * 100) if total > 0 else 0
    print(f"   Success Rate: {percentage:.1f}%")
    
    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED - READY FOR DEPLOYMENT!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed - Fix before deployment")
        return 1

if __name__ == "__main__":
    print("⏳ Starting server check in 2 seconds...")
    print("   (Make sure uvicorn is running on port 8000)")
    asyncio.run(asyncio.sleep(2))
    
    exit_code = asyncio.run(test_production_ready())
    sys.exit(exit_code)
