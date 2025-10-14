# autodocgpt/agent_core/base_agent.py
"""
===============================================================================
AutoDocGPT - Base Agent Module
===============================================================================

This module defines the core communication interface between the AutoDocGPT agent
and the OpenRouter API (a unified access layer for multiple large language models,
including GPT-4, Claude, and Gemini).

Key Responsibilities:
---------------------
1. Manage the connection configuration:
   - Loads the API base URL and key from environment variables or provided arguments.
   - Handles authentication headers and request setup.

2. Define the `Prompt` dataclass:
   - Represents the structured prompt (messages, tools, metadata) sent to the model.

3. Implement the `OpenRouterClient` class:
   - Sends chat completion requests to the OpenRouter endpoint.
   - Supports tool/function calling responses.
   - Returns either plain model output or structured tool invocation data.

Usage Example:
--------------
from autodocgpt.agent_core.base_agent import OpenRouterClient, Prompt

client = OpenRouterClient()
prompt = Prompt(messages=[{"role": "user", "content": "Summarize this project"}])
response = client.complete(prompt, model="gpt-4o")
print(response)

Environment Variables:
----------------------
- OPENROUTER_API_KEY   → Your OpenRouter API key
- OPENROUTER_API_BASE  → (Optional) Custom base URL, defaults to https://openrouter.ai/api/v1

===============================================================================
"""

import os
import json
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Load environment variables from .env file if present
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Prompt:
    """Represents the structure of a conversation sent to OpenRouter API."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class OpenRouterClient:
    """Handles interaction with the OpenRouter API."""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.base_url = base_url or os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OpenRouter API key not provided. Set OPENROUTER_API_KEY in your environment.")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, prompt: Prompt, model: str = "gpt-4o", max_tokens: int = 1024):
        """Send the messages and tools to OpenRouter API and return a structured response."""
        payload = {
            "model": model,
            "messages": prompt.messages,
            "max_tokens": max_tokens
        }

        if prompt.tools:
            payload["tools"] = prompt.tools

        response = requests.post(f"{self.base_url}/chat/completions",
                                 headers=self._headers(),
                                 json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter API Error {response.status_code}: {response.text}")

        data = response.json()
        message = data["choices"][0]["message"]

        # If model called a tool
        if "tool_calls" in message:
            tool_call = message["tool_calls"][0]
            return json.dumps({
                "tool": tool_call["function"]["name"],
                "args": json.loads(tool_call["function"]["arguments"])
            })
        else:
            return message.get("content", "")
