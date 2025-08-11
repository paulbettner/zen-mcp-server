"""
Server-wide defaults configuration for Zen MCP Server.

This module defines the recommended defaults that should be communicated
to all AI agents connecting to the server. These defaults are optimized
for best performance and should be used unless users explicitly request otherwise.
"""

# Server-wide recommended defaults
SERVER_DEFAULTS = {
    "model": "gpt-5",
    "temperature": 0.5,
    "thinking_mode": "high",
    "use_websearch": True,
    
    # Tool-specific default models (override global default)
    "tool_models": {
        "debug": "gemini-2.5-pro",  # Debug benefits from Gemini's large context
        "codereview": "gpt-5",
        "analyze": "gpt-5",
    },
    
    # Messages to communicate to AI agents
    "enforcement_message": (
        "IMPORTANT: Always use these defaults unless the user EXPLICITLY "
        "requests otherwise (e.g., 'use o3 model' or 'set temperature to 0.8'). "
        "These defaults are optimized for best performance."
    ),
    
    "short_message": "DEFAULT: gpt-5, temp=0.5, thinking=high",
    
    "tool_description_suffix": (
        " | DEFAULTS: model=gpt-5, temperature=0.5, thinking_mode=high. "
        "Always use these unless user explicitly requests otherwise."
    ),
    
    # Model-specific defaults
    "model_defaults": {
        "gpt-5": {
            "temperature": 0.5,
            "thinking_mode": "high"
        },
        "o3": {
            "temperature": 0.3,
            "thinking_mode": "max"  # O3 benefits from max thinking
        },
        "gemini-2.5-pro": {
            "temperature": 0.5,
            "thinking_mode": "medium"
        }
    }
}

def get_default_for_model(model: str, setting: str):
    """Get the default setting for a specific model."""
    model_defaults = SERVER_DEFAULTS.get("model_defaults", {})
    model_settings = model_defaults.get(model, {})
    return model_settings.get(setting, SERVER_DEFAULTS.get(setting))

def format_defaults_for_description():
    """Format defaults for inclusion in tool descriptions."""
    return (
        f"[DEFAULTS: model={SERVER_DEFAULTS['model']}, "
        f"temp={SERVER_DEFAULTS['temperature']}, "
        f"thinking={SERVER_DEFAULTS['thinking_mode']}]"
    )

def get_model_field_description():
    """Get the description for model field in schemas."""
    return (
        f"AI model to use. DEFAULT: {SERVER_DEFAULTS['model']} "
        f"(ALWAYS use {SERVER_DEFAULTS['model']} unless user explicitly "
        f"requests another model like 'use o3' or 'try gemini')"
    )

def get_temperature_field_description():
    """Get the description for temperature field in schemas."""
    return (
        f"Response creativity (0-1). DEFAULT: {SERVER_DEFAULTS['temperature']} "
        f"(use default unless user explicitly requests like 'temperature 0.8')"
    )

def get_thinking_field_description():
    """Get the description for thinking_mode field in schemas."""
    return (
        f"Thinking depth: minimal (0.5%), low (8%), medium (33%), high (67%), max (100%). "
        f"DEFAULT: {SERVER_DEFAULTS['thinking_mode']} "
        f"(use default unless user explicitly requests like 'minimal thinking')"
    )