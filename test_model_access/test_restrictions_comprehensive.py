#!/usr/bin/env python3
"""Comprehensive test of model restrictions through actual MCP server."""

import json
import os
import subprocess
import sys

# Important: Do NOT set ZEN_MCP_TEST_MODE for this test
# We want to test the actual production restrictions
if "ZEN_MCP_TEST_MODE" in os.environ:
    del os.environ["ZEN_MCP_TEST_MODE"]


def call_mcp_server(tool_name, arguments):
    """Call the MCP server with a tool request."""
    # Prepare MCP requests
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    initialized_notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}

    tool_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    # Combine messages
    messages = [
        json.dumps(init_request),
        json.dumps(initialized_notification),
        json.dumps(tool_request),
    ]

    input_data = "\n".join(messages) + "\n"

    # Call server
    try:
        result = subprocess.run(
            [sys.executable, "server.py"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        # Parse the response
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if line.strip() and line.startswith("{"):
                try:
                    response = json.loads(line)
                    if response.get("id") == 2:
                        return response
                except json.JSONDecodeError:
                    pass
        return None
    except Exception as e:
        print(f"Exception calling server: {e}")
        return None


def test_model(model_name, should_work=True):
    """Test a specific model."""
    print(f"\nTesting model: {model_name}")
    print("-" * 40)

    # Test with chat tool
    response = call_mcp_server("chat", {"prompt": f"Testing {model_name} - just say 'OK'", "model": model_name})

    if not response:
        print("❌ No response from server")
        return False

    if "error" in response:
        print(f"❌ Server error: {response['error']}")
        return False

    if "result" in response:
        result = response["result"]
        if "content" in result and len(result["content"]) > 0:
            content = result["content"][0].get("text", "")
            try:
                # Parse the JSON response from the tool
                tool_response = json.loads(content)
                status = tool_response.get("status")

                if status == "error":
                    error_msg = tool_response.get("content", "")
                    if should_work:
                        print(f"❌ Model blocked when it should work: {error_msg}")
                        return False
                    else:
                        print(f"✅ Model correctly blocked: {error_msg}")
                        return True
                else:
                    if should_work:
                        model_used = tool_response.get("metadata", {}).get("model_used", "unknown")
                        print(f"✅ Model worked successfully (used: {model_used})")
                        return True
                    else:
                        print("❌ Model worked when it should be blocked!")
                        print(f"   Response: {tool_response}")
                        return False
            except json.JSONDecodeError:
                print(f"⚠️  Could not parse tool response: {content[:200]}...")
                return False

    print("❌ Unexpected response format")
    return False


def test_auto_mode():
    """Test auto mode model selection."""
    print("\nTesting AUTO mode")
    print("-" * 40)

    response = call_mcp_server("chat", {"prompt": "Testing auto mode - just say 'OK'", "model": "auto"})

    if not response:
        print("❌ No response from server")
        return False

    if "error" in response:
        print(f"❌ Server error: {response['error']}")
        return False

    if "result" in response:
        result = response["result"]
        if "content" in result and len(result["content"]) > 0:
            content = result["content"][0].get("text", "")
            try:
                tool_response = json.loads(content)
                if tool_response.get("status") != "error":
                    model_used = tool_response.get("metadata", {}).get("model_used", "unknown")
                    allowed_models = ["o3", "o3-pro", "gemini-2.5-pro", "pro"]
                    if model_used in allowed_models:
                        print(f"✅ Auto mode selected allowed model: {model_used}")
                        return True
                    else:
                        print(f"❌ Auto mode selected disallowed model: {model_used}")
                        return False
                else:
                    print(f"❌ Auto mode failed: {tool_response.get('content', '')}")
                    return False
            except json.JSONDecodeError:
                print("⚠️  Could not parse tool response")
                return False

    return False


def test_listmodels():
    """Test the listmodels tool to see what models are reported as available."""
    print("\nTesting listmodels tool")
    print("-" * 40)

    response = call_mcp_server("listmodels", {"model": "dummy"})

    if not response:
        print("❌ No response from server")
        return False

    if "result" in response:
        result = response["result"]
        if "content" in result and len(result["content"]) > 0:
            content = result["content"][0].get("text", "")
            print("Models reported as available:")
            print(content[:1000] + "..." if len(content) > 1000 else content)
            return True

    return False


def main():
    print("Comprehensive Model Restrictions Test")
    print("=" * 60)

    # Test listmodels first to see what's available
    test_listmodels()

    # Test allowed models
    print("\n\nTesting ALLOWED models:")
    print("=" * 60)
    allowed_results = []
    for model in ["o3", "o3-pro", "gemini-2.5-pro", "pro"]:
        allowed_results.append(test_model(model, should_work=True))

    # Test blocked models
    print("\n\nTesting BLOCKED models:")
    print("=" * 60)
    blocked_results = []
    for model in ["o4-mini", "gpt-4", "claude-opus", "gemini-2.5-flash", "flash", "mistral", "grok-3", "llama3.2"]:
        blocked_results.append(test_model(model, should_work=False))

    # Test auto mode
    print("\n")
    auto_result = test_auto_mode()

    # Summary
    print("\n\nTest Summary:")
    print("=" * 60)
    allowed_passed = sum(allowed_results)
    blocked_passed = sum(blocked_results)
    print(f"Allowed models: {allowed_passed}/{len(allowed_results)} passed")
    print(f"Blocked models: {blocked_passed}/{len(blocked_results)} passed")
    print(f"Auto mode: {'PASSED' if auto_result else 'FAILED'}")

    total_passed = allowed_passed + blocked_passed + (1 if auto_result else 0)
    total_tests = len(allowed_results) + len(blocked_results) + 1

    if total_passed == total_tests:
        print(f"\n✅ ALL TESTS PASSED ({total_passed}/{total_tests})")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED ({total_passed}/{total_tests})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
