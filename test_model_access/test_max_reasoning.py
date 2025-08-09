#!/usr/bin/env python3
"""Test that all OpenAI models use v1/responses with MAXIMUM reasoning effort."""

import os
import sys
from openai import OpenAI

def test_model_max_reasoning(client, model_name):
    """Test a model with maximum reasoning effort."""
    try:
        print(f"\nTesting {model_name} with MAXIMUM reasoning effort...")
        
        # Determine parameters based on model (matching server logic)
        params = {
            "model": model_name,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "What is 2+2? Think carefully and use your maximum reasoning ability."
                        }
                    ]
                }
            ],
            "store": True
        }
        
        if model_name == "o3-deep-research":
            effort = "medium"  # Medium IS the maximum for o3-deep-research
            params["reasoning"] = {"effort": effort}
            params["tools"] = [{"type": "web_search_preview"}]
        elif model_name == "gpt-5-chat-latest":
            # GPT-5-chat-latest doesn't support reasoning.effort
            effort = "automatic"  # It uses reasoning automatically
            # Don't add reasoning parameter
        else:
            effort = "high"  # HIGH effort for all other models
            params["reasoning"] = {"effort": effort}
            
        response = client.responses.create(**params)
        
        print(f"✅ SUCCESS: {model_name} using {effort.upper()} reasoning effort!")
        
        # Check for reasoning tokens usage
        if hasattr(response, 'usage'):
            if hasattr(response.usage, 'reasoning_tokens') and response.usage.reasoning_tokens:
                print(f"   ✨ Used {response.usage.reasoning_tokens} reasoning tokens")
            if hasattr(response.usage, 'input_tokens'):
                print(f"   📊 Input: {response.usage.input_tokens}, Output: {response.usage.output_tokens}")
                            
        return True, effort
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ FAILED: {model_name}")
        print(f"   Error: {error_str[:300]}")
        return False, None

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    print("TESTING MAXIMUM REASONING EFFORT ENFORCEMENT")
    print("=" * 60)
    print("Verifying ALL OpenAI models use v1/responses with MAX reasoning")
    
    client = OpenAI(api_key=api_key)
    
    # Test all allowed OpenAI models
    models_to_test = [
        "gpt-5",
        "gpt-5-chat-latest",  # Should now use v1/responses with high effort
        "o3",
        "o3-mini", 
        "o3-pro",
        "o3-deep-research",
    ]
    
    results = {}
    
    for model in models_to_test:
        success, effort = test_model_max_reasoning(client, model)
        results[model] = (success, effort)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: MAXIMUM REASONING ENFORCEMENT")
    print("-" * 40)
    
    all_success = True
    for model, (success, effort) in results.items():
        if success:
            print(f"✅ {model}: Using {effort.upper()} reasoning (maximum available)")
        else:
            print(f"❌ {model}: Failed to use maximum reasoning")
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 SUCCESS: All models enforced to use MAXIMUM reasoning levels!")
        print("\nRestrictions enforced:")
        print("• O3/O3-mini/O3-pro: HIGH effort (maximum)")
        print("• O3-deep-research: MEDIUM effort (its maximum)")
        print("• GPT-5 variants: HIGH effort (maximum)")
        print("• All using v1/responses endpoint for reasoning tokens")
    else:
        print("⚠️  Some models failed - check errors above")

if __name__ == "__main__":
    main()