#!/usr/bin/env python3
"""Test o3-deep-research model availability."""

import os

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

    print("Testing O3-Deep-Research Model Availability")
    print("=" * 60)

    # Create client
    client = OpenAI(api_key=api_key)

    # Test various o3-deep-research variations
    models_to_test = [
        "o3-deep-research",
        "o3-deep",
        "deep-research",
        "o3-deep-research-2025-08-07",  # Try dated version
    ]

    results = {}

    for model in models_to_test:
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

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 40)

    available_models = [m for m, v in results.items() if v is True]
    if available_models:
        print(f"✅ Available O3-Deep-Research models: {', '.join(available_models)}")
    else:
        print("❌ O3-Deep-Research model is not currently accessible via the API")

if __name__ == "__main__":
    main()
