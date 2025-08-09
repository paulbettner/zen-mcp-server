#!/usr/bin/env python3
"""Test if GPT-5 and O3 models work with v1/responses endpoint for thinking/streaming."""

import os
import sys
from openai import OpenAI

def test_model_with_responses(client, model_name):
    """Test a model with the responses endpoint."""
    try:
        print(f"\nTesting {model_name} via responses.create()...")
        
        # Determine the appropriate effort level based on model
        if "deep-research" in model_name:
            effort = "medium"  # O3-deep-research only supports medium
            tools = [{"type": "web_search_preview"}]  # Required for deep research
        else:
            effort = "low"  # Try low for other models
            tools = None  # No tools required for non-deep-research models
        
        params = {
            "model": model_name,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "What is 2+2? Just say the number."
                        }
                    ]
                }
            ],
            "reasoning": {"effort": effort},
            "store": True
        }
        
        if tools:
            params["tools"] = tools
            
        response = client.responses.create(**params)
        
        print(f"✅ SUCCESS: {model_name} works with v1/responses!")
        print(f"   Response ID: {response.id}")
        
        # Extract the output
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if content_item.type == 'output_text':
                            print(f"   Response: {content_item.text[:100]}")
                            
        # Check for reasoning tokens
        if hasattr(response, 'reasoning_content'):
            print(f"   ✨ Reasoning tokens available!")
        elif hasattr(response, 'usage') and hasattr(response.usage, 'reasoning_tokens'):
            if response.usage.reasoning_tokens > 0:
                print(f"   ✨ Used {response.usage.reasoning_tokens} reasoning tokens")
                            
        return True
        
    except Exception as e:
        error_str = str(e)
        if "does not support" in error_str or "not supported" in error_str:
            print(f"❌ {model_name} does not support v1/responses endpoint")
            print(f"   Error: {error_str[:200]}")
        elif "unsupported value" in error_str.lower():
            print(f"⚠️  {model_name} has parameter restrictions")
            print(f"   Error: {error_str[:200]}")
        else:
            print(f"❌ {model_name} failed with error")
            print(f"   Error: {error_str[:200]}")
        return False

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    print("Testing Models with v1/responses Endpoint")
    print("=" * 60)
    print("Testing if GPT-5 and O3 models support the responses endpoint")
    print("for extended thinking/reasoning capabilities...")
    
    client = OpenAI(api_key=api_key)
    
    # Models to test
    models_to_test = [
        "gpt-5-chat-latest",  # GPT-5 with thinking support
        "gpt-5",              # GPT-5 base
        "o3",                 # O3 reasoning model
        "o3-mini",            # O3 mini variant
        "o3-pro",             # O3 pro (we know this works)
        "o3-deep-research",   # O3 deep research (we know this works)
    ]
    
    results = {}
    
    for model in models_to_test:
        success = test_model_with_responses(client, model)
        results[model] = success
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 40)
    
    working_models = [m for m, success in results.items() if success]
    failed_models = [m for m, success in results.items() if not success]
    
    if working_models:
        print(f"✅ Models supporting v1/responses: {', '.join(working_models)}")
        
    if failed_models:
        print(f"❌ Models NOT supporting v1/responses: {', '.join(failed_models)}")
        
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("-" * 40)
    
    if "gpt-5-chat-latest" in working_models or "gpt-5" in working_models:
        print("• GPT-5 supports v1/responses - consider using it for reasoning tokens")
    
    if "o3" in working_models:
        print("• O3 supports v1/responses - consider using it for better reasoning")
        
    if failed_models:
        print(f"• Continue using v1/chat/completions for: {', '.join(failed_models)}")

if __name__ == "__main__":
    main()