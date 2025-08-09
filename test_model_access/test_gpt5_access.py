#!/usr/bin/env python3
"""Test if gpt-5 model is accessible through the zen-mcp-server."""

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

def test_model(model_name):
    """Test if a model is accessible."""
    response = call_mcp_server('chat', {
        'prompt': f'Testing {model_name} - just say OK',
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
    print("Testing GPT-5 Model Access")
    print("=" * 60)
    
    # Test main model names
    models_to_test = ['gpt-5', 'gpt5', 'GPT-5', 'gpt-5-mini', 'gpt5-mini']
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        print("-" * 40)
        
        success, message = test_model(model)
        
        if success is True:
            print(f"✅ Model {model} is ACCESSIBLE! (resolved to: {message})")
        elif success is False:
            if "not available" in message.lower():
                print(f"❌ Model {model} is BLOCKED by restrictions")
                print(f"   Error: {message[:200]}")
            else:
                print(f"❌ Model {model} failed with error: {message[:200]}")
        else:
            print(f"⚠️  Model {model}: {message}")
    
    # Check what models are available
    print("\n" + "=" * 60)
    print("Checking available models via listmodels...")
    print("-" * 40)
    
    response = call_mcp_server('listmodels', {'model': 'dummy'})
    if response and 'result' in response:
        result = response['result']
        if 'content' in result and len(result['content']) > 0:
            content = result['content'][0].get('text', '')
            # Parse the JSON response
            try:
                models_response = json.loads(content)
                models_content = models_response.get('content', '')
                
                # Check if gpt-5 is mentioned
                if 'gpt-5' in models_content.lower() or 'gpt5' in models_content.lower():
                    print("✅ GPT-5 is listed in available models!")
                    # Extract just the OpenAI section
                    if "## OpenAI" in models_content:
                        openai_section = models_content.split("## OpenAI")[1].split("##")[0]
                        print("\nOpenAI Models Section:")
                        print(openai_section[:500])
                else:
                    print("❌ GPT-5 is NOT listed in available models")
                    print("\nAvailable models summary:")
                    if "**Models**:" in models_content:
                        # Show a summary of available models
                        for line in models_content.split('\n'):
                            if '`' in line and 'context' in line:
                                print(f"  {line.strip()}")
            except:
                print("Could not parse listmodels response")

if __name__ == "__main__":
    main()