#!/usr/bin/env python3
"""Test GPT-5 and O3-Deep-Research with updated API key."""

import os
import sys

from openai import OpenAI

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
        return True, f"Model is available! Response: {response.choices[0].message.content}"
    except Exception as e:
        error_str = str(e)
        if "does not have access" in error_str.lower():
            return False, "Project does not have access to this model"
        elif "does not exist" in error_str.lower():
            return False, "Model does not exist"
        elif "only supported in v1/responses" in error_str.lower():
            return False, "Model requires v1/responses endpoint (not chat/completions)"
        elif "insufficient_quota" in error_str.lower():
            return True, "Model exists but quota exceeded"
        elif "rate_limit" in error_str.lower():
            return True, "Model exists but rate limited"
        else:
            return None, f"Error: {error_str[:200]}"

def main():
    # Check if API key is provided as argument or in environment
    api_key = os.getenv("OPENAI_API_KEY")

    if len(sys.argv) > 1:
        print("⚠️  Using API key from command line argument")
        api_key = sys.argv[1]
    elif api_key:
        print("Using API key from environment variable")
    else:
        print("❌ No API key found. Set OPENAI_API_KEY or pass as argument")
        print("Usage: python test_new_api_key.py [API_KEY]")
        return

    print("Testing GPT-5 and O3-Deep-Research Access")
    print("=" * 60)

    # Create client
    client = OpenAI(api_key=api_key)

    # Models to test
    models_to_test = [
        ("gpt-5-chat-latest", "GPT-5 Chat Latest"),
        ("gpt-5", "GPT-5"),
        ("o3-deep-research", "O3 Deep Research"),
    ]

    results = {}

    for model, display_name in models_to_test:
        print(f"\nTesting: {display_name} ({model})")
        print("-" * 40)

        available, message = test_model_availability(client, model)
        results[model] = (available, message)

        if available is True:
            print(f"✅ SUCCESS: {display_name} is AVAILABLE - {message}")
        elif available is False:
            print(f"❌ FAILED: {display_name} - {message}")
        else:
            print(f"⚠️  ERROR: {display_name} - {message}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 40)

    working = [m for m, (status, _) in results.items() if status is True]
    if working:
        print(f"✅ Working models: {', '.join(working)}")
    else:
        print("❌ No models are currently accessible with this API key")

    # Check if we need to update configuration
    if "gpt-5-chat-latest" in working or "gpt-5" in working:
        print("\n✅ GPT-5 is accessible! The model configuration is correct.")

    if "o3-deep-research" in [m for m, (s, msg) in results.items() if s is False and "v1/responses" in msg]:
        print("\n⚠️  O3-Deep-Research exists but needs v1/responses endpoint (not currently supported)")

if __name__ == "__main__":
    main()
