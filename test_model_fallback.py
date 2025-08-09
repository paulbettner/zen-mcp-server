#!/usr/bin/env python3
"""Test the model fallback mechanism."""

import json
import subprocess
import sys


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


def test_invalid_model_fallback(tool_name, invalid_model):
    """Test that an invalid model falls back to GPT-5."""
    print(f"\n{'='*70}")
    print(f"Testing {tool_name} with invalid model: '{invalid_model}'")
    print("-" * 70)
    
    # Prepare arguments based on tool
    if tool_name == "chat":
        arguments = {
            'prompt': 'Say "Hello from fallback test"',
            'model': invalid_model
        }
    elif tool_name == "thinkdeep":
        arguments = {
            'step': 'Test if fallback works',
            'step_number': 1,
            'total_steps': 1,
            'next_step_required': False,
            'findings': 'Testing fallback mechanism',
            'model': invalid_model
        }
    elif tool_name == "consensus":
        arguments = {
            'step': 'Should we use model fallback?',
            'step_number': 1,
            'total_steps': 1,
            'next_step_required': False,
            'models': [{'model': invalid_model}],
            'findings': 'Testing fallback'
        }
    elif tool_name == "debug":
        arguments = {
            'step': 'Debug fallback test',
            'step_number': 1,
            'total_steps': 1,
            'next_step_required': False,
            'findings': 'Testing fallback',
            'model': invalid_model
        }
    elif tool_name == "analyze":
        arguments = {
            'step': 'Analyze fallback',
            'step_number': 1,
            'total_steps': 1,
            'next_step_required': False,
            'findings': 'Testing fallback',
            'model': invalid_model
        }
    else:
        print(f"⚠️  Unknown tool: {tool_name}")
        return False
    
    response = call_mcp_server(tool_name, arguments)
    
    if response and 'result' in response:
        result = response['result']
        if 'content' in result and len(result['content']) > 0:
            content = result['content'][0].get('text', '')
            try:
                tool_response = json.loads(content)
                
                # Check for fallback warning
                if 'model_fallback_warning' in tool_response:
                    print(f"✅ FALLBACK WORKED!")
                    print(f"   Warning: {tool_response['model_fallback_warning'][:150]}...")
                    
                    # Check if actual model is GPT-5
                    metadata = tool_response.get('metadata', {})
                    model_used = metadata.get('model_used', metadata.get('model_name', 'unknown'))
                    print(f"   Model used: {model_used}")
                    
                    if 'gpt-5' in model_used.lower():
                        print(f"   ✅ Correctly fell back to GPT-5")
                        return True
                    else:
                        print(f"   ❌ Expected GPT-5 but got: {model_used}")
                        return False
                        
                # Check if error mentions model not available
                elif 'error' in tool_response:
                    error_msg = str(tool_response['error'])
                    if 'not available' in error_msg:
                        print(f"❌ FALLBACK FAILED - Got error instead of fallback")
                        print(f"   Error: {error_msg[:200]}")
                        return False
                        
                # Success without warning might mean the model exists
                else:
                    print(f"⚠️  No fallback warning - model might exist?")
                    metadata = tool_response.get('metadata', {})
                    model_used = metadata.get('model_used', metadata.get('model_name', 'unknown'))
                    print(f"   Model used: {model_used}")
                    return None
                    
            except json.JSONDecodeError:
                print(f"❌ Could not parse response as JSON")
                print(f"   Response: {content[:200]}")
                return False
    else:
        print(f"❌ No valid response from server")
        if response and 'error' in response:
            print(f"   Error: {response['error']}")
        return False


def main():
    print("MODEL FALLBACK MECHANISM TEST")
    print("=" * 80)
    print("Testing that invalid models fall back to GPT-5 with maximum reasoning")
    
    # Test various invalid model names
    invalid_models = [
        "flash",           # Model mentioned in user's example
        "invalid-model",   # Obviously invalid
        "gpt-4",          # Not in allowlist
        "claude-3",       # Not available
        "o1-preview",     # Old model not in list
    ]
    
    # Test with different tools
    tools_to_test = ["chat", "thinkdeep", "consensus", "debug", "analyze"]
    
    results = {}
    
    for tool in tools_to_test:
        print(f"\n{'='*80}")
        print(f"Testing {tool.upper()} Tool")
        print("=" * 80)
        
        for model in invalid_models:
            result = test_invalid_model_fallback(tool, model)
            results[f"{tool}:{model}"] = result
            
            # Small delay between tests
            import time
            time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    uncertain = sum(1 for r in results.values() if r is None)
    
    print(f"\nPassed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    if uncertain > 0:
        print(f"Uncertain: {uncertain}/{len(results)}")
    
    # Details
    if failed > 0:
        print("\nFailed tests:")
        for key, result in results.items():
            if result is False:
                tool, model = key.split(':')
                print(f"  - {tool} with '{model}'")
    
    if passed == len(results):
        print("\n🎉 SUCCESS: All invalid models correctly fall back to GPT-5!")
    else:
        print(f"\n⚠️  Some tests failed - fallback mechanism may need adjustment")
        
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()