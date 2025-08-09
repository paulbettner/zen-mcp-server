#!/usr/bin/env python3
"""Comprehensive test of all allowed models in the allowlist."""

import os
import json
import subprocess
import sys
import time

def call_mcp_server(tool_name, arguments):
    """Call the MCP server with a tool request."""
    init_request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05',
            'capabilities': {'tools': {}},
            'clientInfo': {'name': 'test-client', 'version': '1.0.0'},
        },
    }
    
    initialized_notification = {'jsonrpc': '2.0', 'method': 'notifications/initialized'}
    
    tool_request = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': arguments
        },
    }
    
    messages = [
        json.dumps(init_request),
        json.dumps(initialized_notification),
        json.dumps(tool_request),
    ]
    
    input_data = '\n'.join(messages) + '\n'
    
    result = subprocess.run(
        [sys.executable, 'server.py'],
        input=input_data,
        text=True,
        capture_output=True,
        timeout=60,
    )
    
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if line.strip() and line.startswith('{'):
            try:
                response = json.loads(line)
                if response.get('id') == 2:
                    return response
            except json.JSONDecodeError:
                pass
    return None

def test_model(model_name, provider=""):
    """Test if a model is accessible."""
    response = call_mcp_server('chat', {
        'prompt': f'Testing {model_name} - just say OK in one word',
        'model': model_name
    })
    
    if response and 'result' in response:
        result = response['result']
        if 'content' in result and len(result['content']) > 0:
            content = result['content'][0].get('text', '')
            try:
                tool_response = json.loads(content)
                status = tool_response.get('status')
                if status == 'error':
                    error_msg = tool_response.get('content', '')
                    return False, error_msg
                else:
                    model_used = tool_response.get('metadata', {}).get('model_used', 'unknown')
                    return True, model_used
            except:
                return None, f"Could not parse response: {content[:200]}"
    elif response and 'error' in response:
        return False, response['error']
    else:
        return None, "No valid response"

def main():
    print("COMPREHENSIVE ALLOWLIST TEST")
    print("=" * 80)
    print("Testing all models that should be allowed per Paul's requirements:")
    print("- GPT-5 (gpt-5-chat-latest)")
    print("- O3 models (o3, o3-pro)")
    print("- Gemini 2.5 Pro") 
    print("- Claude Opus 4.1 (via OpenRouter)")
    print("=" * 80)
    
    # Models to test based on Paul's requirements
    test_cases = [
        # GPT-5 models
        ("gpt-5", "OpenAI"),
        ("gpt5", "OpenAI"),
        ("gpt-5-chat-latest", "OpenAI"),
        
        # O3 models
        ("o3", "OpenAI"),
        ("o3-pro", "OpenAI"),
        
        # O3-deep-research (may not work with chat completions)
        ("o3-deep-research", "OpenAI"),
        
        # Gemini 2.5 Pro
        ("gemini-2.5-pro", "Google"),
        ("pro", "Google"),  # Alias for gemini-2.5-pro
        
        # Claude Opus 4.1 via OpenRouter
        ("anthropic/claude-opus-4.1", "OpenRouter"),
        ("opus", "OpenRouter"),  # Alias
        ("claude-opus", "OpenRouter"),  # Another alias
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for model, provider in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {model} ({provider})")
        print("-" * 60)
        
        success, message = test_model(model)
        results[model] = (success, message, provider)
        
        if success is True:
            print(f"✅ PASS: {model} is accessible (resolved to: {message})")
            passed += 1
        elif success is False:
            if "not allowed" in message.lower() or "blocked by restrictions" in message.lower():
                print(f"❌ FAIL: {model} is BLOCKED by restrictions")
                print(f"   Error: {message[:200]}")
                failed += 1
            elif "o3-deep-research" in model and "only supported in v1/responses" in message:
                print(f"⚠️  INFO: {model} requires different API endpoint (v1/responses)")
                # Don't count as failure since it's a known limitation
            else:
                print(f"❌ FAIL: {model} failed with error: {message[:200]}")
                failed += 1
        else:
            print(f"⚠️  UNKNOWN: {model}: {message}")
            failed += 1
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    
    # Group by provider
    by_provider = {}
    for model, (success, message, provider) in results.items():
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append((model, success))
    
    print("\nBy Provider:")
    for provider, models in sorted(by_provider.items()):
        working = [m for m, s in models if s is True]
        blocked = [m for m, s in models if s is False]
        print(f"\n{provider}:")
        if working:
            print(f"  ✅ Working: {', '.join(working)}")
        if blocked:
            print(f"  ❌ Blocked: {', '.join(blocked)}")
    
    # Final status
    print("\n" + "=" * 80)
    if failed == 0:
        print("✅ ALL TESTS PASSED - All allowed models are accessible!")
    else:
        print(f"❌ TESTS FAILED - {failed} models are not accessible")
        print("\nBlocked models need investigation:")
        for model, (success, message, provider) in results.items():
            if success is False and "o3-deep-research" not in model:
                print(f"  - {model} ({provider}): {message[:100]}")

if __name__ == "__main__":
    main()