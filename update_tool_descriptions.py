#!/usr/bin/env python3
"""Update all tool descriptions to include server defaults."""

import os
import re

# Tools to update with their description method patterns
TOOLS_TO_UPDATE = {
    "analyze.py": "AnalyzeTool",
    "codereview.py": "CodeReviewTool", 
    "consensus.py": "ConsensusTool",
    "planner.py": "PlannerTool",
    "precommit.py": "PrecommitTool",
    "refactor.py": "RefactorTool",
    "secaudit.py": "SecauditTool",
    "testgen.py": "TestGenTool",
    "tracer.py": "TracerTool",
}

# The code to insert at the beginning of get_description
DEFAULTS_CODE = '''try:
            from config_defaults import SERVER_DEFAULTS
            defaults_msg = (
                f" [DEFAULTS: model={SERVER_DEFAULTS['model']}, "
                f"thinking={SERVER_DEFAULTS['thinking_mode']}] "
                f"{SERVER_DEFAULTS['enforcement_message']}"
            )
        except ImportError:
            defaults_msg = ""
            '''

def update_tool_file(filepath, tool_class):
    """Update a tool file to include defaults in description."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'from config_defaults import SERVER_DEFAULTS' in content:
        print(f"✓ {filepath} already updated")
        return
    
    # Find the get_description method
    pattern = r'(def get_description\(self\) -> str:\s*\n\s*return \()'
    
    # Check if file has get_description
    if not re.search(pattern, content):
        print(f"⚠️  {filepath} doesn't have standard get_description pattern")
        return
    
    # Replace to add defaults
    def replacement(match):
        indent = "        "  # Assuming standard indentation
        defaults_with_indent = '\n'.join(indent + line if line else '' 
                                        for line in DEFAULTS_CODE.split('\n'))
        return match.group(1) + '\n' + defaults_with_indent + '\n        base_desc = ('
    
    updated_content = re.sub(pattern, replacement, content)
    
    # Also need to update the return statement
    # Find the closing of the description
    updated_content = re.sub(
        r'(\n\s*"[^"]*"\s*\))',  # Find the last line of description
        r'\1 + defaults_msg',
        updated_content,
        count=1
    )
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated {filepath}")

def main():
    tools_dir = "tools"
    
    for filename, tool_class in TOOLS_TO_UPDATE.items():
        filepath = os.path.join(tools_dir, filename)
        if os.path.exists(filepath):
            update_tool_file(filepath, tool_class)
        else:
            print(f"❌ {filepath} not found")

if __name__ == "__main__":
    main()