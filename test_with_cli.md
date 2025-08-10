# Testing Zen MCP with Claude CLI

## Test 1: Model Fallback
Test that an invalid model like "flash" falls back to a working model:

```bash
claude
```
Then type:
```
Use the zen chat tool with model "flash" and prompt "Test fallback - should use gpt-5 or another model instead"
```

Expected: Should see a warning about model fallback and use GPT-5 or another available model.

## Test 2: Large Context (>60k tokens)
Test that we can send prompts larger than 60k tokens:

```bash
claude
```
Then type:
```
Create a string of 250,000 'x' characters (about 62k tokens). Use the zen chat tool with model "o3" to analyze how many characters are in that string.
```

Expected: Should accept and process the large prompt without a 60k token limit error.

## Test 3: Multiple Tools with Fallback
Test that fallback works across different zen tools:

```bash
claude
```
Then type:
```
Use the zen debug tool with model "invalid-model" to debug why 2+2 might not equal 4. Set step_number=1, total_steps=1, next_step_required=false, findings="Testing fallback"
```

Expected: Should see fallback warning and use an available model.