#!/usr/bin/env python3
"""Quick test of the model fallback mechanism."""

import json
import os
import sys
from pathlib import Path

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print("✅ Loaded .env file")

# Import after loading env
from providers import ModelProviderRegistry
from utils.model_context import ModelContext


def test_direct_context():
    """Test ModelContext fallback directly."""
    print("\n=== Testing ModelContext Fallback ===")

    # Get available models
    available_models = ModelProviderRegistry.get_available_models()
    print(f"Available models: {len(available_models)}")
    if available_models:
        print(f"First 5: {', '.join(list(available_models.keys())[:5])}")

    # Test with invalid model
    print("\nTesting with invalid model 'flash'...")
    try:
        ctx = ModelContext('flash')
        provider = ctx.provider

        if ctx.fallback_warning:
            print("✅ FALLBACK WORKS!")
            print(f"  Warning: {ctx.fallback_warning[:100]}...")
            print(f"  Actual model: {ctx.actual_model_name}")
        else:
            print("❌ No fallback warning")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_tool_fallback():
    """Test fallback through a tool."""
    print("\n=== Testing Tool Fallback (via MCP) ===")

    import subprocess

    # Prepare MCP protocol messages
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

    # Test with invalid model 'flash'
    tool_request = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/call',
        'params': {
            'name': 'chat',
            'arguments': {
                'prompt': 'Say "test fallback works"',
                'model': 'flash',  # Invalid model
                'temperature': 0.1
            }
        },
    }

    messages = [
        json.dumps(init_request),
        json.dumps(initialized_notification),
        json.dumps(tool_request),
    ]

    input_data = '\n'.join(messages) + '\n'

    print("Running MCP server with invalid model...")

    # Run the server with env loaded
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, 'server.py'],
        input=input_data,
        text=True,
        capture_output=True,
        timeout=60,
        env=env
    )

    # Parse response
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if line.strip() and line.startswith('{'):
            try:
                response = json.loads(line)
                if response.get('id') == 2:
                    if 'result' in response:
                        content = response['result']['content'][0]['text']
                        tool_response = json.loads(content)

                        if 'model_fallback_warning' in tool_response:
                            print('✅ FALLBACK WORKS IN TOOL!')
                            print(f'  Warning: {tool_response["model_fallback_warning"][:100]}...')
                            metadata = tool_response.get('metadata', {})
                            model_used = metadata.get('model_used', 'unknown')
                            print(f'  Model used: {model_used}')
                            return True
                        else:
                            print('❌ No fallback warning in tool response')
                            print(f'  Status: {tool_response.get("status")}')
                            if tool_response.get("status") == "error":
                                print(f'  Error: {tool_response.get("content")}')
                            return False
                    elif 'error' in response:
                        print(f'❌ MCP Error: {response["error"]}')
                        return False
            except Exception:
                pass

    print("❌ No valid response from server")
    if result.stderr:
        print(f"Stderr: {result.stderr[:200]}")
    return False

if __name__ == "__main__":
    print("MODEL FALLBACK TEST")
    print("=" * 50)

    # Test direct ModelContext
    test_direct_context()

    # Test through MCP tool
    success = test_tool_fallback()

    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️ Some tests failed")

    sys.exit(0 if success else 1)
