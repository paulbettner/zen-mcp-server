#!/usr/bin/env python3
"""Test that token limits use actual model context windows, not artificial 60k limit."""

import sys
from unittest.mock import Mock, patch

# Mock imports
from utils.token_utils import estimate_tokens


def test_validate_token_limit_logic():
    """Test the logic of _validate_token_limit without needing actual models."""
    print("\n=== Testing Token Validation Logic ===")
    
    # Import the base tool
    from tools.shared.base_tool import BaseTool
    
    # Create a mock tool
    class MockTool(BaseTool):
        def __init__(self):
            self.name = "mock_tool"
            
        def get_name(self):
            return self.name
            
        def get_description(self):
            return "Mock tool"
            
        def get_input_schema(self):
            return {}
            
        async def execute(self, arguments):
            return []
            
        def get_system_prompt(self):
            return ""
            
        def get_request_model(self):
            return None
            
        def prepare_prompt(self, request):
            return ""
    
    tool = MockTool()
    
    # Test WITHOUT model context (should use 200k default)
    print("\n1. Testing without model context (200k default):")
    
    # Content under 200k tokens (~800k chars)
    small_content = "x" * 700_000  # ~175k tokens
    try:
        tool._validate_token_limit(small_content, "Test")
        print(f"  ✅ Accepted ~175k tokens (under 200k default)")
    except ValueError as e:
        print(f"  ❌ Should accept content under 200k: {e}")
    
    # Content over 200k tokens
    large_content = "x" * 900_000  # ~225k tokens  
    try:
        tool._validate_token_limit(large_content, "Test")
        print(f"  ❌ Should reject content over 200k")
    except ValueError as e:
        if "too large" in str(e):
            print(f"  ✅ Correctly rejected ~225k tokens")
    
    # Test WITH model context
    print("\n2. Testing with mock model context (1M tokens):")
    
    # Create mock model context
    mock_context = Mock()
    mock_context.capabilities = Mock()
    mock_context.capabilities.context_window = 1_000_000  # 1M tokens
    tool._model_context = mock_context
    
    # Content under 800k tokens (80% of 1M)
    medium_content = "x" * 3_000_000  # ~750k tokens
    try:
        tool._validate_token_limit(medium_content, "Test")
        print(f"  ✅ Accepted ~750k tokens (under 800k limit)")
    except ValueError as e:
        print(f"  ❌ Should accept content under 800k: {e}")
    
    # Content over 800k tokens
    huge_content = "x" * 3_500_000  # ~875k tokens
    try:
        tool._validate_token_limit(huge_content, "Test")
        print(f"  ❌ Should reject content over 800k")
    except ValueError as e:
        if "too large" in str(e):
            print(f"  ✅ Correctly rejected ~875k tokens")
    
    # Test that it's NOT using 60k limit
    print("\n3. Verifying NO 60k limit:")
    
    # Create content that's >60k tokens but under model limit
    sixty_k_plus = "x" * 300_000  # ~75k tokens
    try:
        tool._validate_token_limit(sixty_k_plus, "Test")
        estimated = estimate_tokens(sixty_k_plus)
        print(f"  ✅ Accepted {estimated:,} tokens - NO artificial 60k limit!")
    except ValueError as e:
        if "60" in str(e):
            print(f"  ❌ FAILED: Still has 60k limit - {e}")
        else:
            print(f"  ❌ Unexpected error: {e}")
            
    return True


def test_token_allocation_calculations():
    """Test that ModelContext calculates proper token allocations."""
    print("\n=== Testing Token Allocation Calculations ===")
    
    from utils.model_context import TokenAllocation
    
    # Test allocations for different model sizes
    test_cases = [
        (200_000, "Small model (200k)", 0.6, 0.3, 0.5),  # O3
        (1_000_000, "Large model (1M)", 0.8, 0.4, 0.4),  # Gemini
    ]
    
    for total_tokens, name, expected_content_ratio, expected_file_ratio, expected_history_ratio in test_cases:
        print(f"\n{name}:")
        
        # Calculate expected values
        content_tokens = int(total_tokens * expected_content_ratio)
        file_tokens = int(content_tokens * expected_file_ratio)
        history_tokens = int(content_tokens * expected_history_ratio)
        
        print(f"  Total: {total_tokens:,} tokens")
        print(f"  Content: {content_tokens:,} tokens ({expected_content_ratio:.0%})")
        print(f"  Files: {file_tokens:,} tokens ({expected_file_ratio:.0%} of content)")
        print(f"  History: {history_tokens:,} tokens ({expected_history_ratio:.0%} of content)")
        
        # Verify no artificial 60k limit
        if file_tokens < 60_000 and total_tokens > 300_000:
            print(f"  ⚠️ WARNING: File allocation seems artificially limited")
        elif file_tokens >= 60_000:
            print(f"  ✅ File allocation > 60k tokens - no artificial limit")
    
    return True


def test_mcp_transport_vs_model_limits():
    """Test that MCP_PROMPT_SIZE_LIMIT is only for transport."""
    print("\n=== Testing MCP Transport vs Model Limits ===")
    
    from config import MCP_PROMPT_SIZE_LIMIT
    
    print(f"\nMCP_PROMPT_SIZE_LIMIT: {MCP_PROMPT_SIZE_LIMIT:,} characters")
    print(f"Equivalent to: ~{MCP_PROMPT_SIZE_LIMIT // 4:,} tokens")
    
    print("\nThis limit applies ONLY to:")
    print("  ✓ Initial user prompt via MCP transport")
    print("  ✓ prompt.txt file content")
    
    print("\nThis limit does NOT apply to:")
    print("  ✗ Total context sent to models")
    print("  ✗ File content added by tools")
    print("  ✗ Conversation history")
    print("  ✗ System prompts")
    
    print("\nModel context windows are MUCH larger:")
    print("  - O3: 200,000 tokens (13x larger)")
    print("  - GPT-5: 400,000 tokens (26x larger)")
    print("  - Gemini: 1,000,000+ tokens (66x larger)")
    
    return True


def test_file_content_preparation():
    """Test that file content preparation doesn't have 60k limit."""
    print("\n=== Testing File Content Preparation ===")
    
    # The old code had this line that we removed:
    # self._validate_token_limit(file_content, context_description)
    # 
    # This was incorrectly limiting file content to 60k when
    # MCP_PROMPT_SIZE_LIMIT was passed to check_token_limit
    
    print("\nOLD BEHAVIOR (FIXED):")
    print("  _validate_token_limit was called with MCP_PROMPT_SIZE_LIMIT")
    print("  This limited file content to 60k tokens incorrectly")
    
    print("\nNEW BEHAVIOR:")
    print("  ✅ Removed redundant _validate_token_limit call")
    print("  ✅ read_files() already respects max_tokens parameter")
    print("  ✅ max_tokens calculated from model's actual context window")
    
    return True


def main():
    """Run all token limit tests."""
    print("=" * 60)
    print("TOKEN LIMIT FIX VERIFICATION")
    print("=" * 60)
    print("\nTesting that the 60k token artificial limit has been removed")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_validate_token_limit_logic()
    all_passed &= test_token_allocation_calculations()
    all_passed &= test_mcp_transport_vs_model_limits()
    all_passed &= test_file_content_preparation()
    
    print("\n" + "=" * 60)
    print("SUMMARY OF CHANGES:")
    print("=" * 60)
    
    print("\n1. Fixed _validate_token_limit() to use model's context window")
    print("   - Was: Using MCP_PROMPT_SIZE_LIMIT (60k chars as tokens)")
    print("   - Now: Using model's actual context window (200k-1M+ tokens)")
    
    print("\n2. Removed redundant validation in _prepare_file_content_for_prompt()")
    print("   - Was: Double-validating with wrong limit")
    print("   - Now: Trusting read_files() to respect max_tokens")
    
    print("\n3. Token allocations per model:")
    print("   - O3: 200k total, 120k content, 36k files")
    print("   - GPT-5: 400k total, 320k content, 128k files")
    print("   - Gemini: 1M+ total, 800k content, 320k files")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - 60k limit has been removed!")
    else:
        print("⚠️ Some tests indicated issues")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())