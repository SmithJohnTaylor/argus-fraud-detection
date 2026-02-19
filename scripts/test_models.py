#!/usr/bin/env python3
"""
Test available models on Together AI
"""

import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

async def test_models():
    """Test common models to see which ones work"""
    
    load_dotenv()
    api_key = os.getenv('TOGETHER_API_KEY')
    
    if not api_key:
        print("❌ No Together AI API key found")
        return
    
    # Common models to test
    models_to_test = [
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "meta-llama/Llama-2-7b-chat-hf",
        "meta-llama/Llama-2-13b-chat-hf", 
        "togethercomputer/RedPajama-INCITE-Chat-3B-v1",
        "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
        "Open-Orca/Mistral-7B-OpenOrca",
        "teknium/OpenHermes-2.5-Mistral-7B",
        "microsoft/DialoGPT-medium"
    ]
    
    base_url = "https://api.together.xyz/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "messages": [{"role": "user", "content": "Hello, test message"}],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    print(f"🔍 Testing {len(models_to_test)} models...")
    
    async with aiohttp.ClientSession() as session:
        for model in models_to_test:
            try:
                payload = {**test_payload, "model": model}
                
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        print(f"✅ {model} - WORKS")
                    else:
                        error_text = await response.text()
                        print(f"❌ {model} - {response.status}: {error_text[:100]}...")
                        
            except asyncio.TimeoutError:
                print(f"⏰ {model} - TIMEOUT")
            except Exception as e:
                print(f"❌ {model} - ERROR: {str(e)[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_models())