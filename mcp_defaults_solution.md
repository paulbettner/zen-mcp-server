# MCP Defaults Communication Solution

## Best Approaches to Inform AI Agents About Defaults

MCP provides several mechanisms to communicate defaults and preferences to AI agents connecting to the zen-mcp server. Here are the most effective approaches:

## 1. Tool Descriptions (Most Effective) ✅

**Implementation**: Update each tool's `get_description()` method to explicitly state defaults.

```python
def get_description(self) -> str:
    return (
        "CHAT & COLLABORATION - General conversation and thinking partner. "
        "DEFAULT MODEL: gpt-5 | DEFAULT TEMPERATURE: 0.5 | DEFAULT THINKING: high. "
        "Use for: brainstorming, second opinions, explanations, comparisons. "
        "IMPORTANT: Always use gpt-5 unless user explicitly requests another model."
    )
```

**Benefits**:
- Visible immediately when AI lists tools
- Clear and explicit about expectations
- Works with all MCP clients

## 2. Input Schema Descriptions with Defaults ✅

**Implementation**: Enhance field descriptions in `get_input_schema()` to emphasize defaults.

```python
def get_input_schema(self) -> dict[str, Any]:
    properties = {
        "model": {
            "type": "string",
            "description": "AI model to use. DEFAULT: gpt-5 (ALWAYS use gpt-5 unless user explicitly requests otherwise)",
            "default": "gpt-5",
            "enum": ["gpt-5", "o3", "gemini-2.5-pro"],
        },
        "temperature": {
            "type": "number",
            "description": "Response creativity (0-1). DEFAULT: 0.5 (use default unless user specifies)",
            "default": 0.5,
            "minimum": 0,
            "maximum": 1
        },
        "thinking_mode": {
            "type": "string",
            "description": "Thinking depth. DEFAULT: high (use 'high' unless user requests otherwise)",
            "default": "high",
            "enum": ["minimal", "low", "medium", "high", "max"]
        }
    }
```

**Benefits**:
- JSON Schema `default` field is standardized
- Descriptions reinforce the defaults
- AI agents can see defaults when examining tool schemas

## 3. Server Initialization Message ✅

**Implementation**: Send a notification when client connects with default preferences.

```python
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List tools and communicate server defaults."""
    
    # Add a special "server-defaults" tool that communicates preferences
    tools = [
        Tool(
            name="_server_defaults",
            description=(
                "⚠️ ZEN MCP SERVER DEFAULTS - PLEASE FOLLOW: "
                "1. ALWAYS use model 'gpt-5' unless user explicitly requests another model. "
                "2. ALWAYS use temperature 0.5 unless user explicitly requests otherwise. "
                "3. ALWAYS use thinking_mode 'high' unless user explicitly requests otherwise. "
                "These defaults are optimized for best results. Only deviate when user specifically asks."
            ),
            inputSchema={"type": "object", "properties": {}}
        )
    ]
    
    # Add regular tools
    tools.extend([...])
    return tools
```

## 4. MCP Prompts with Defaults ✅

**Implementation**: Use MCP prompts to provide pre-configured templates.

```python
@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    prompts = [
        Prompt(
            name="chat_default",
            description="Chat with optimal defaults (gpt-5, temp=0.5, thinking=high)",
            arguments=[
                PromptArgument(
                    name="prompt",
                    description="Your message",
                    required=True
                )
            ]
        )
    ]
    return prompts

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict) -> GetPromptResult:
    if name == "chat_default":
        return GetPromptResult(
            description="Chat with server defaults",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Use zen chat with model='gpt-5', temperature=0.5, thinking_mode='high', prompt='{arguments.get('prompt', '')}'"
                    )
                )
            ]
        )
```

## 5. Tool Annotations (MCP Extension) ✅

**Implementation**: Add custom annotations to tools.

```python
def get_annotations(self) -> dict:
    return {
        "defaults": {
            "model": "gpt-5",
            "temperature": 0.5,
            "thinking_mode": "high"
        },
        "usage_notes": "Always use these defaults unless user explicitly overrides"
    }
```

## 6. Validation with Warnings ✅

**Implementation**: Return warnings when non-default values are used without explicit user request.

```python
def execute(self, request):
    # Check if non-default model was used
    if request.model != "gpt-5" and not self._user_explicitly_requested_model(request):
        self.add_warning(
            "⚠️ Using non-default model. Server recommends 'gpt-5' for best results. "
            "Only use other models when user explicitly requests them."
        )
```

## Recommended Implementation Strategy

### Phase 1: Immediate Changes (Quick Wins)
1. **Update all tool descriptions** to include DEFAULT statements
2. **Add default values to schema fields** with emphatic descriptions
3. **Create a SERVER_DEFAULTS constant** in config.py

### Phase 2: Enhanced Communication
1. **Add a _server_defaults pseudo-tool** that appears first in tool list
2. **Implement validation warnings** when non-defaults are used
3. **Create default prompt templates** for common operations

### Phase 3: Smart Defaults
1. **Auto-correction**: If model not specified, always use gpt-5
2. **Contextual defaults**: Different defaults for different tool categories
3. **User preference tracking**: Remember user's explicit choices

## Example Implementation

```python
# config.py
SERVER_DEFAULTS = {
    "model": "gpt-5",
    "temperature": 0.5,
    "thinking_mode": "high",
    "enforcement_message": (
        "IMPORTANT: Always use these defaults unless the user EXPLICITLY "
        "requests otherwise. These are optimized for best performance."
    )
}

# tools/chat.py
def get_description(self) -> str:
    defaults = SERVER_DEFAULTS
    return (
        f"CHAT & COLLABORATION - General conversation and thinking partner. "
        f"DEFAULTS: model={defaults['model']}, temp={defaults['temperature']}, "
        f"thinking={defaults['thinking_mode']}. {defaults['enforcement_message']} "
        f"Use for: brainstorming, second opinions, explanations."
    )

def get_input_schema(self) -> dict[str, Any]:
    defaults = SERVER_DEFAULTS
    return {
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": f"Model to use. DEFAULT: {defaults['model']} - ALWAYS use this unless user explicitly requests another",
                "default": defaults['model']
            },
            # ... other fields with defaults
        }
    }
```

## Testing the Implementation

1. **Connect with Claude CLI** and ask it to list tools
2. **Verify descriptions** include DEFAULT statements
3. **Test compliance** by asking Claude to use a zen tool without specifying model
4. **Check if defaults are followed** in the execution

## Expected AI Behavior After Implementation

When an AI agent connects and sees these defaults:
1. It will use `gpt-5` by default for all operations
2. It will use `temperature=0.5` unless asked otherwise
3. It will use `thinking_mode=high` unless specified
4. It will only deviate when user says things like:
   - "Use o3 model for this"
   - "Set temperature to 0.8"
   - "Use minimal thinking mode"

This approach ensures AI agents are well-informed about server preferences while still allowing user override when explicitly requested.