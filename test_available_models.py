#!/usr/bin/env python3
"""Check what models are available."""

import sys
import os
from pathlib import Path

# Load environment
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

print("=" * 60)
print("CHECKING AVAILABLE MODELS")
print("=" * 60)

# Check API keys
print("\nAPI Keys present:")
for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", 
            "TOGETHERAI_API_KEY", "DEEPSEEK_API_KEY", "HYPERBOLIC_API_KEY"]:
    if os.getenv(key):
        print(f"  ✅ {key}: Present")
    else:
        print(f"  ❌ {key}: Missing")

# Check available models
print("\nChecking model registry...")
from providers.registry import ModelProviderRegistry

providers = ModelProviderRegistry.list_all_providers()
print(f"\nActive providers: {providers}")

print("\nChecking each model from ALLOWED_MODELS...")
from config import ALLOWED_MODELS

for model in ALLOWED_MODELS:
    provider = ModelProviderRegistry.get_provider_for_model(model)
    if provider:
        print(f"  ✅ {model}: Available via {provider.get_provider_type().value}")
    else:
        print(f"  ❌ {model}: Not available")

print("\n" + "=" * 60)
print("TESTING FALLBACK WITH AVAILABLE MODELS")
print("=" * 60)

# Find an available model
available_model = None
for model in ALLOWED_MODELS:
    provider = ModelProviderRegistry.get_provider_for_model(model)
    if provider:
        available_model = model
        break

if available_model:
    print(f"\nUsing {available_model} for testing...")
    
    from utils.model_context import ModelContext
    
    print("\n1. Testing invalid model 'flash' (should fallback):")
    try:
        ctx = ModelContext("flash")
        if ctx.fallback_warning:
            print(f"   ✅ FALLBACK WORKED: {ctx.fallback_warning}")
            print(f"   Actual model used: {ctx.actual_model_name}")
        else:
            print(f"   ⚠️ No fallback warning but model loaded: {ctx.actual_model_name}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print(f"\n2. Testing valid model '{available_model}':")
    try:
        ctx = ModelContext(available_model)
        if ctx.fallback_warning:
            print(f"   ⚠️ Unexpected fallback: {ctx.fallback_warning}")
        else:
            print(f"   ✅ Model loaded directly: {ctx.actual_model_name}")
            if ctx.capabilities and ctx.capabilities.context_window:
                print(f"   Context window: {ctx.capabilities.context_window:,} tokens")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
else:
    print("\n❌ No models available - please check API keys in .env file")