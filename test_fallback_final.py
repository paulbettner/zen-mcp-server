#!/usr/bin/env python3
"""Final test of model fallback mechanism."""

import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv('.env')

# Initialize providers like server.py does
from providers.registry import ModelProviderRegistry

# Import provider modules to ensure they register (from server.py)
if os.getenv("OPENAI_API_KEY"):
    from providers.openai_provider import OpenAIModelProvider
    
if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
    from providers.gemini import GeminiModelProvider
    
if os.getenv("OPENROUTER_API_KEY"):
    from providers.openrouter import OpenRouterProvider
    
if os.getenv("XAI_API_KEY"):
    from providers.xai import XAIModelProvider
    
if os.getenv("CUSTOM_API_URL"):
    from providers.custom import CustomProvider
    
if os.getenv("DIAL_API_URL"):
    from providers.dial import DIALModelProvider

print("=" * 60)
print("TESTING MODEL FALLBACK MECHANISM")
print("=" * 60)

# Check available models
available = ModelProviderRegistry.get_available_models()
print(f"\nAvailable models: {len(available)}")
for i, model in enumerate(list(available.keys())[:10]):
    print(f"  {i+1}. {model}")
if len(available) > 10:
    print(f"  ... and {len(available) - 10} more")

# Test fallback
print("\n" + "=" * 60)
print("TEST: Invalid model 'flash' should fall back")
print("=" * 60)

from utils.model_context import ModelContext

print("\nCreating ModelContext with 'flash'...")
ctx = ModelContext('flash')

# Access provider to trigger fallback
provider = ctx.provider

if ctx.fallback_warning:
    print("\n✅ FALLBACK SUCCESSFUL!")
    print(f"Warning: {ctx.fallback_warning}")
    print(f"Actual model: {ctx.actual_model_name}")
else:
    print("\n❌ FALLBACK FAILED")
    print(f"No fallback warning - model: {ctx.actual_model_name}")

print("\n" + "=" * 60)
print("TEST: Large context (>60k tokens)")
print("=" * 60)

# Test with a valid model
valid_model = None
for model in ["gpt-5", "o3", "gemini-2.5-pro", "pro"]:
    if ModelProviderRegistry.get_provider_for_model(model):
        valid_model = model
        break

if valid_model:
    print(f"\nUsing {valid_model} for large context test...")
    ctx = ModelContext(valid_model)
    
    # Check context window
    window = ctx.capabilities.context_window
    print(f"Context window: {window:,} tokens")
    
    if window > 60_000:
        print(f"✅ Context window > 60k tokens!")
    else:
        print(f"⚠️ Context window is only {window:,} tokens")
else:
    print("❌ No valid models available for testing")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nBoth features should now be working:")
print("1. Model fallback for invalid models")
print("2. Large context windows (>60k tokens)")