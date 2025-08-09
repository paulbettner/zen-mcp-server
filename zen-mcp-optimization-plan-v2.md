# Zen MCP Server Optimization Plan v2
*Keeping tools separate for better AI performance*

## Overview
This plan outlines how to reduce the zen-mcp-server token footprint from ~42,000 tokens to ~12,000 tokens (71% reduction) while maintaining all functionality and keeping tools distinct for clarity.

## Current Issues
1. **Model enum duplication**: The same 44-line model enum (1,500 tokens) is repeated in 11 tools = 15,000 wasted tokens
2. **Verbose descriptions**: Tool and parameter descriptions are unnecessarily wordy  
3. **Excessive parameter documentation**: Implementation details that Claude doesn't need
4. **Redundant schema definitions**: Same parameters defined multiple times

## Implementation Steps

### 1. Replace Repository (First Step)
```bash
# Update claude_desktop_config.json
{
  "mcpServers": {
    "zen": {
      "command": "/Users/paulbettner/Projects/zen-mcp-server-fork/.zen_venv/bin/python",
      "args": [
        "/Users/paulbettner/Projects/zen-mcp-server-fork/server.py"
      ]
    }
  }
}
```

### 2. Model Enum Optimization (15,000 tokens saved)

**Current**: Every tool has the full model enum
```python
"model": {
    "description": "IMPORTANT: Use the model specified...[2000+ chars]",
    "enum": ["anthropic/claude-3-haiku", ... 44 models ...],
    "type": "string"
}
```

**Optimized**: Reference-based approach
```python
# In each tool:
"model": {
    "description": "AI model to use (see listmodels for available options)",
    "type": "string"
}

# Only in listmodels tool:
# Keep the full enum and detailed model descriptions
```

### 3. Tool Description Compression (8,000 tokens saved)

Keep all tools separate but compress descriptions to essential information:

**thinkdeep**:
- Before: "COMPREHENSIVE INVESTIGATION & REASONING - Multi-stage workflow..." (500+ words)
- After: "Multi-stage investigation for complex problems. Enforces step-by-step analysis with evidence gathering."

**debug**:
- Before: "DEBUG & ROOT CAUSE ANALYSIS - Systematic self-investigation..." (400+ words)
- After: "Root cause analysis tool. Step-by-step debugging with hypothesis testing."

**analyze**:
- Before: "COMPREHENSIVE ANALYSIS WORKFLOW - Step-by-step code analysis..." (400+ words)
- After: "Code analysis workflow. Systematic evaluation of architecture, performance, and quality."

**codereview**:
- Before: "COMPREHENSIVE CODE REVIEW WORKFLOW - Step-by-step code review..." (450+ words)
- After: "Structured code review. Identifies issues, patterns, and improvement opportunities."

**chat**:
- Before: "GENERAL CHAT & COLLABORATIVE THINKING - Use the AI model..." (200+ words)
- After: "General conversation and collaborative problem-solving."

**consensus**:
- Before: "MULTI-MODEL CONSENSUS - Gather diverse perspectives..." (300+ words) 
- After: "Gather perspectives from multiple AI models. Supports stance configuration."

**planner**:
- Before: "INTERACTIVE SEQUENTIAL PLANNER - Break down complex tasks..." (350+ words)
- After: "Sequential task planning with revision and branching support."

**testgen**:
- Before: "COMPREHENSIVE TEST GENERATION - Creates thorough test suites..." (250+ words)
- After: "Generate comprehensive test suites with edge case coverage."

**refactor**:
- Before: "COMPREHENSIVE REFACTORING WORKFLOW - Step-by-step refactoring..." (300+ words)
- After: "Systematic refactoring analysis. Identifies code smells and improvement opportunities."

**tracer**:
- Before: "STEP-BY-STEP CODE TRACING WORKFLOW - Systematic code analysis..." (300+ words)
- After: "Trace code execution flow and dependencies. Modes: precision (methods) or dependencies (modules)."

### 4. Parameter Description Optimization (5,000 tokens saved)

Compress all parameter descriptions to essential information:

**Before**:
```python
"confidence": {
    "description": "Indicate your current confidence in the hypothesis. Use: 'exploring' (starting out), 'low' (early idea), 'medium' (some supporting evidence), 'high' (strong evidence), 'certain' (only when the root cause and minimal fix are both confirmed). Do NOT use 'certain' unless the issue can be fully resolved with a fix, use 'high' instead when not 100% sure. Using 'certain' prevents you from taking assistance from another thought-partner.",
    "enum": ["exploring", "low", "medium", "high", "certain"],
    "type": "string"
}
```

**After**:
```python
"confidence": {
    "description": "Current confidence level in findings",
    "enum": ["exploring", "low", "medium", "high", "certain"],
    "type": "string"
}
```

**More examples**:
- `files_checked`: "List all files examined" (was 50+ words)
- `findings`: "Discoveries from this step" (was 100+ words)  
- `next_step_required`: "Continue to next step?" (was 30+ words)
- `thinking_mode`: "Thinking depth level" (was 50+ words)
- `use_websearch`: "Enable web search?" (was 80+ words)

### 5. Schema Reuse (2,000 tokens saved)

Define common parameters once and reference them:

```python
# Define once at module level
COMMON_SCHEMAS = {
    "model": {"description": "AI model to use (see listmodels)", "type": "string"},
    "confidence": {"description": "Confidence level", "enum": ["exploring", "low", "medium", "high", "certain"], "type": "string"},
    "thinking_mode": {"description": "Thinking depth", "enum": ["minimal", "low", "medium", "high", "max"], "type": "string"},
    "temperature": {"description": "Response creativity (0-1)", "type": "number", "minimum": 0, "maximum": 1},
    "continuation_id": {"description": "Thread ID to continue conversation", "type": "string"},
    "use_websearch": {"description": "Enable web search?", "type": "boolean", "default": true}
}
```

### 6. Remove Redundant Information (2,000 tokens saved)

- Remove "IMPORTANT:" prefixes and warnings
- Remove repeated instructions about step enforcement  
- Remove verbose examples within descriptions
- Remove implementation details about how tools work internally

### 7. Final Tool List (All Preserved)

1. **thinkdeep** - Complex problem investigation
2. **debug** - Root cause analysis  
3. **analyze** - Code quality assessment
4. **codereview** - Comprehensive code review
5. **chat** - General conversation
6. **consensus** - Multi-model perspectives
7. **planner** - Sequential task planning
8. **precommit** - Pre-commit validation
9. **testgen** - Test generation
10. **refactor** - Refactoring analysis
11. **tracer** - Code flow tracing
12. **listmodels** - Available models (with full details)
13. **version** - Server information

## Expected Results

- **Before**: ~42,000 tokens
- **After**: ~12,000 tokens  
- **Reduction**: 71%
- **Overall prompt reduction**: 30% (30,000 tokens saved)

## Key Benefits of Keeping Tools Separate

1. **Clearer Intent**: AI models can better understand what's being asked
2. **Better Tool Selection**: Distinct names help with appropriate tool choice
3. **Easier Debugging**: Clear which tool was used for what purpose
4. **No Migration Needed**: Existing workflows continue to work
5. **Semantic Clarity**: Each tool has a specific, well-defined purpose

## Testing Plan

1. Verify all tools load with compressed descriptions
2. Ensure model selection works without local enum validation
3. Test that parameter help is still sufficient
4. Confirm thread continuation works
5. Validate token count reduction
6. Ensure no functionality loss despite compressed descriptions