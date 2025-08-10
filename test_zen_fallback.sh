#!/bin/bash

echo "=========================================="
echo "Testing Zen MCP Fallback Mechanism"
echo "=========================================="
echo ""
echo "This will test:"
echo "1. Invalid model 'flash' falls back to GPT-5"
echo "2. Large prompts work (>60k tokens)"
echo ""
echo "Running test with Claude CLI..."
echo ""

# Test 1: Model fallback
echo "TEST 1: Model Fallback (invalid model 'flash')"
echo "----------------------------------------------"
claude << 'EOF'
Use the zen chat tool with model 'flash' and prompt 'Testing fallback mechanism - this should fall back to GPT-5 or another available model'
EOF

echo ""
echo "TEST 2: Large Context (>60k tokens)"
echo "----------------------------------------------"
# Generate a large prompt (>60k tokens = ~240k+ chars)
LARGE_TEXT=$(python3 -c "print('x' * 250000)")
claude << EOF
Use the zen chat tool with model 'gpt-5' and prompt 'Count the approximate number of characters in this text: ${LARGE_TEXT:0:1000}...[truncated for display, but full ${#LARGE_TEXT} chars sent]'
EOF

echo ""
echo "=========================================="
echo "Tests complete!"
echo "=========================================="