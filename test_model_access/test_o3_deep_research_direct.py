#!/usr/bin/env python3
"""Test o3-deep-research model directly with v1/responses endpoint."""

import os
import sys
from openai import OpenAI

def test_o3_deep_research():
    """Test o3-deep-research with the responses endpoint."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    print("Testing O3-Deep-Research with v1/responses endpoint")
    print("=" * 60)
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Use the responses endpoint directly with web_search_preview tool
        print("Calling o3-deep-research via responses.create() with web_search_preview tool...")
        response = client.responses.create(
            model="o3-deep-research",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "What is 2+2? Just say the number. No need to search the web."
                        }
                    ]
                }
            ],
            reasoning={"effort": "medium"},  # O3-deep-research only supports medium effort
            store=True,
            tools=[{"type": "web_search_preview"}]  # Required for deep research models
        )
        
        print("✅ SUCCESS: o3-deep-research is working!")
        print(f"Response ID: {response.id}")
        
        # Extract the output
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if content_item.type == 'output_text':
                            print(f"Response: {content_item.text}")
                            return True
        
        print("⚠️  Got response but couldn't extract output")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_o3_deep_research()
    sys.exit(0 if success else 1)