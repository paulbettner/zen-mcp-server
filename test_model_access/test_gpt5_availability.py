#!/usr/bin/env python3
"""Test which GPT-5 models are actually available via OpenAI API."""

import os
import sys
from openai import OpenAI
import httpx

# Temporarily disable restrictions for this test
os.environ["ZEN_MCP_TEST_MODE"] = "true"
# Clear any model restrictions
for key in ["OPENAI_ALLOWED_MODELS", "GOOGLE_ALLOWED_MODELS", "XAI_ALLOWED_MODELS", "OPENROUTER_ALLOWED_MODELS"]:
    if key in os.environ:
        del os.environ[key]

def test_model_availability(client, model_name):
    """Test if a model is available by making a minimal API call."""
    try:
        # Try a minimal completion request
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5
        )
        return True, "Model is available and working"
    except Exception as e:
        error_str = str(e)
        if "model does not exist" in error_str.lower() or "not found" in error_str.lower():
            return False, "Model does not exist"
        elif "insufficient_quota" in error_str.lower():
            return True, "Model exists but quota exceeded"
        elif "rate_limit" in error_str.lower():
            return True, "Model exists but rate limited"
        else:
            return None, f"Error: {error_str[:200]}"

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    print("Testing GPT-5 Model Availability via OpenAI API")
    print("=" * 60)
    
    # Create client
    client = OpenAI(api_key=api_key)
    
    # Models to test
    gpt5_models = [
        "gpt-5",
        "gpt-5-mini", 
        "gpt-5-nano",
        "gpt5",  # Test alias
        "gpt5-mini",  # Test alias
    ]
    
    results = {}
    
    for model in gpt5_models:
        print(f"\nTesting model: {model}")
        print("-" * 40)
        
        available, message = test_model_availability(client, model)
        results[model] = available
        
        if available is True:
            print(f"✅ {model}: AVAILABLE - {message}")
        elif available is False:
            print(f"❌ {model}: NOT AVAILABLE - {message}")
        else:
            print(f"⚠️  {model}: UNKNOWN - {message}")
    
    # Also test what models we can list
    print("\n" + "=" * 60)
    print("Attempting to list models via API...")
    print("-" * 40)
    
    try:
        models_list = client.models.list()
        gpt5_found = []
        for model in models_list.data:
            if "gpt-5" in model.id.lower() or "gpt5" in model.id.lower():
                gpt5_found.append(model.id)
                print(f"✅ Found GPT-5 model in list: {model.id}")
        
        if not gpt5_found:
            print("❌ No GPT-5 models found in model list")
            print("\nSample of available models:")
            for i, model in enumerate(models_list.data[:10]):
                print(f"  - {model.id}")
            if len(models_list.data) > 10:
                print(f"  ... and {len(models_list.data) - 10} more")
    except Exception as e:
        print(f"⚠️  Could not list models: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 40)
    
    available_models = [m for m, v in results.items() if v is True]
    if available_models:
        print(f"✅ Available GPT-5 models: {', '.join(available_models)}")
        print("\nThese models should be added to the allowed list.")
    else:
        print("❌ No GPT-5 models are currently available via the OpenAI API")
        print("This could mean:")
        print("  1. GPT-5 is not yet released")
        print("  2. Your API key doesn't have access")
        print("  3. The models have different names than expected")

if __name__ == "__main__":
    main()