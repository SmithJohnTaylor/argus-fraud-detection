#!/usr/bin/env python3
"""
Test current Together AI serverless models for chat completions
"""

import os
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

async def test_serverless_models():
    """Test current serverless models available on Together AI"""
    
    load_dotenv()
    api_key = os.getenv('TOGETHER_API_KEY')
    
    if not api_key:
        print("❌ No Together AI API key found")
        return
    
    # Current serverless models based on Together AI docs (2025)
    models_to_test = [
        # Working models
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        
        # Latest Llama models
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "meta-llama/Llama-3.1-8B-Instruct-Turbo",
        "meta-llama/Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Llama-3.1-405B-Instruct-Turbo",
        
        # DeepSeek models
        "deepseek-ai/deepseek-r1-distill-llama-70b",
        "deepseek-ai/deepseek-r1-distill-qwen-14b",
        
        # Qwen models
        "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        
        # Mistral models
        "mistralai/Mistral-7B-Instruct-v0.3",
        "mistralai/Mistral-Small-Instruct-2411",
        
        # Free models
        "meta-llama/Llama-Vision-Free",
        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"
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
    
    print(f"🔍 Testing {len(models_to_test)} serverless models...")
    print("=" * 60)
    
    working_models = []
    
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
                        print(f"✅ {model}")
                        working_models.append(model)
                    else:
                        error_text = await response.text()
                        print(f"❌ {model} - {response.status}")
                        if "non-serverless" in error_text:
                            print(f"   └─ Not available on serverless")
                        elif "Unable to access" in error_text:
                            print(f"   └─ Access denied")
                        else:
                            print(f"   └─ {error_text[:100]}...")
                        
            except asyncio.TimeoutError:
                print(f"⏰ {model} - TIMEOUT")
            except Exception as e:
                print(f"❌ {model} - ERROR: {str(e)[:100]}...")
    
    print("\n" + "=" * 60)
    print(f"✅ Working serverless models ({len(working_models)}):")
    for model in working_models:
        print(f"  - {model}")
    
    return working_models

if __name__ == "__main__":
    asyncio.run(test_serverless_models())