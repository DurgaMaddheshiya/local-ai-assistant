#!/usr/bin/env python3
"""
Quick test script to check available Gemini models
"""
import httpx
import json

API_KEY = "YOUR_GEMINI_API_KEY_HERE"

async def test_gemini():
    # Test different model names
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-pro",
        "gemini-1.0-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro"
    ]
    
    test_payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100}
    }
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=test_payload)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"✅ SUCCESS: {model} works!")
                    result = resp.json()
                    print("Response:", result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", ""))
                else:
                    print(f"❌ FAILED: {resp.status_code}")
                    print("Error:", resp.text[:200])
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini())