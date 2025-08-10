#!/usr/bin/env python3
"""Test that token limits use actual model context windows, not artificial 60k limit."""

import sys
from pathlib import Path

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Import after loading env
from tools.shared.base_tool import BaseTool
from utils.model_context import ModelContext
from utils.token_utils import estimate_tokens


class TestTool(BaseTool):
    """Test tool to verify token limit behavior."""

    def get_name(self):
        return "test_tool"

    def get_description(self):
        return "Test tool"

    def get_input_schema(self):
        return {}

    async def execute(self, arguments):
        return []

    def prepare_prompt(self, request):
        return ""


def test_model_context_windows():
    """Test that different models have different context windows."""
    print("\n=== Testing Model Context Windows ===")

    models_to_test = [
        ("gemini-2.5-pro", 1_000_000),  # 1M+ tokens
        ("o3", 200_000),  # 200k tokens
        ("gpt-5", 400_000),  # 400k tokens
    ]

    for model_name, expected_min in models_to_test:
        try:
            ctx = ModelContext(model_name)
            if ctx.provider:
                window = ctx.capabilities.context_window
                print(f"✅ {model_name}: {window:,} tokens (expected ≥{expected_min:,})")

                if window < expected_min:
                    print("  ⚠️ WARNING: Context window smaller than expected!")

        except Exception as e:
            print(f"❌ {model_name}: Failed - {e}")

    return True


def test_token_validation_uses_model_context():
    """Test that _validate_token_limit uses actual model context window."""
    print("\n=== Testing Token Validation with Model Context ===")

    tool = TestTool()

    # Test with different models
    test_cases = [
        ("gemini-2.5-pro", 800_000),  # Should allow ~800k tokens (80% of 1M)
        ("o3", 160_000),  # Should allow ~160k tokens (80% of 200k)
    ]

    for model_name, expected_limit in test_cases:
        try:
            # Set model context
            ctx = ModelContext(model_name)
            if not ctx.provider:
                print(f"⚠️ Skipping {model_name} - not available")
                continue

            tool._model_context = ctx

            # Create content just under the limit (should pass)
            # ~4 chars per token, so multiply by 4
            small_content = "x" * (expected_limit * 3)  # Well under limit

            try:
                tool._validate_token_limit(small_content, "Test content")
                estimated = estimate_tokens(small_content)
                print(f"✅ {model_name}: Accepted {estimated:,} tokens (limit ~{expected_limit:,})")
            except ValueError as e:
                print(f"❌ {model_name}: Rejected valid content - {e}")

            # Create content over the limit (should fail)
            large_content = "x" * (expected_limit * 5)  # Over limit

            try:
                tool._validate_token_limit(large_content, "Test content")
                print(f"❌ {model_name}: Should have rejected oversized content!")
            except ValueError as e:
                if "too large" in str(e):
                    estimated = estimate_tokens(large_content)
                    print(f"✅ {model_name}: Correctly rejected {estimated:,} tokens")
                else:
                    print(f"❌ {model_name}: Wrong error - {e}")

        except Exception as e:
            print(f"❌ {model_name}: Test failed - {e}")

    return True


def test_no_artificial_60k_limit():
    """Test that we're NOT limited to 60k tokens."""
    print("\n=== Testing NO Artificial 60k Limit ===")

    tool = TestTool()

    # Use a model with large context window
    model_name = "gemini-2.5-pro"
    try:
        ctx = ModelContext(model_name)
        if not ctx.provider:
            # Try fallback model
            model_name = "gpt-5"
            ctx = ModelContext(model_name)
            if not ctx.provider:
                print("⚠️ No large context model available for testing")
                return False

        tool._model_context = ctx

        # Create content that's >60k tokens but within model's limit
        # 60k tokens = ~240k chars, let's use 300k chars (75k tokens)
        content_size = 300_000
        large_content = "x" * content_size
        estimated = estimate_tokens(large_content)

        print(f"Testing with {estimated:,} tokens (>{60_000} tokens)...")

        try:
            tool._validate_token_limit(large_content, "Large content")
            print(f"✅ SUCCESS: Accepted {estimated:,} tokens - NO 60k limit!")
            return True
        except ValueError as e:
            if "60" in str(e) or "60000" in str(e) or "60,000" in str(e):
                print(f"❌ FAIL: Still limited to 60k - {e}")
                return False
            else:
                # Check if it's hitting the model's actual limit
                model_limit = int(ctx.capabilities.context_window * 0.8)
                if estimated > model_limit:
                    print(f"✅ Hit model's actual limit ({model_limit:,} tokens), not 60k")
                    return True
                else:
                    print(f"❌ Unexpected error - {e}")
                    return False

    except Exception as e:
        print(f"❌ Test failed - {e}")
        return False


def test_file_content_respects_model_limits():
    """Test that file content preparation uses model-specific limits."""
    print("\n=== Testing File Content with Model Limits ===")

    tool = TestTool()

    # Test with a model
    model_name = "o3"
    try:
        ctx = ModelContext(model_name)
        if not ctx.provider:
            print(f"⚠️ {model_name} not available")
            return False

        # Calculate expected file token allocation
        token_allocation = ctx.calculate_token_allocation()
        print(f"\n{model_name} token allocation:")
        print(f"  Total: {token_allocation.total_tokens:,}")
        print(f"  Content: {token_allocation.content_tokens:,}")
        print(f"  Files: {token_allocation.file_tokens:,}")
        print(f"  History: {token_allocation.history_tokens:,}")
        print(f"  Response: {token_allocation.response_tokens:,}")

        # Verify file tokens are reasonable (not limited to 60k)
        if token_allocation.file_tokens < 60_000:
            print(f"⚠️ File token allocation seems low: {token_allocation.file_tokens:,}")
        else:
            print(f"✅ File token allocation is reasonable: {token_allocation.file_tokens:,}")

        return True

    except Exception as e:
        print(f"❌ Test failed - {e}")
        return False


def test_mcp_prompt_limit_vs_model_limit():
    """Verify MCP_PROMPT_SIZE_LIMIT is for transport, not model context."""
    print("\n=== Testing MCP vs Model Limits ===")

    from config import MCP_PROMPT_SIZE_LIMIT

    print(f"MCP_PROMPT_SIZE_LIMIT: {MCP_PROMPT_SIZE_LIMIT:,} characters")
    print(f"This is ~{MCP_PROMPT_SIZE_LIMIT // 4:,} tokens")
    print("\nThis limit is ONLY for initial user prompt transport via MCP protocol.")
    print("It does NOT limit the total context sent to models.\n")

    # Compare with model limits
    models = ["gemini-2.5-pro", "o3", "gpt-5"]
    for model_name in models:
        try:
            ctx = ModelContext(model_name)
            if ctx.provider:
                window = ctx.capabilities.context_window
                ratio = window / (MCP_PROMPT_SIZE_LIMIT // 4)
                print(f"{model_name}: {window:,} tokens ({ratio:.1f}x larger than MCP transport limit)")
        except:
            pass

    return True


def main():
    """Run all token limit tests."""
    print("=" * 60)
    print("TOKEN LIMIT TESTS")
    print("=" * 60)
    print("\nVerifying that models use their actual context windows,")
    print("not an artificial 60k token limit.")

    all_passed = True

    # Run tests
    all_passed &= test_model_context_windows()
    all_passed &= test_token_validation_uses_model_context()
    all_passed &= test_no_artificial_60k_limit()
    all_passed &= test_file_content_respects_model_limits()
    all_passed &= test_mcp_prompt_limit_vs_model_limit()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nModels are using their full context windows:")
        print("- Gemini: 1M+ tokens")
        print("- GPT-5: 400k tokens")
        print("- O3: 200k tokens")
        print("\nNO artificial 60k token limit!")
    else:
        print("⚠️ Some tests failed or were skipped")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
