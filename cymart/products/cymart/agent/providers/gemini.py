"""Real Gemini adapter — google-genai SDK with function-calling,
restricted to exactly tools.ALLOWED_TOOLS. Requires GEMINI_API_KEY; the
``google-genai`` package is imported lazily so its absence never breaks
the sandbox default. Enable via:

    CYMART_AGENT_PROVIDER = "products.cymart.agent.providers.gemini.GeminiCompletionProvider"
    GEMINI_API_KEY = "..."  # or the GEMINI_API_KEY env var

No credentials exist in this environment — this class is unexercised by
the test suite (see providers/sandbox.py for what tests run against),
same posture as providers/claude.py and payments.providers for a real
gateway. Both adapters implement the same CompletionProvider interface,
so swapping between them (or between models) is a one-line settings
change — AgentSession and the tool gate never change.
"""

import os
import uuid

from django.conf import settings

from .base import CompletionProvider, CompletionResult, ToolCall

DEFAULT_MODEL = "gemini-3.1-flash-lite"


class GeminiCompletionProvider(CompletionProvider):
    def __init__(self, model: str | None = None):
        self._model = model or getattr(settings, "CYMART_AGENT_GEMINI_MODEL", DEFAULT_MODEL)

    def _client(self):
        from google import genai  # lazy — only needed when this provider is selected

        api_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        return genai.Client(api_key=api_key)

    def complete(self, system_prompt: str, messages: list[dict], tools: list[dict]) -> CompletionResult:
        from google.genai import types

        client = self._client()
        function_declarations = [
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters_json_schema=t["parameters"],
            )
            for t in tools
        ]
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(function_declarations=function_declarations)],
        )

        response = client.models.generate_content(
            model=self._model,
            contents=self._to_gemini_contents(messages),
            config=config,
        )

        calls = response.function_calls or []
        tool_calls = [
            ToolCall(name=c.name, arguments=dict(c.args or {}), id=c.id or str(uuid.uuid4()))
            for c in calls
        ]
        stop_reason = "tool_use" if tool_calls else "end"
        return CompletionResult(text=response.text or "", tool_calls=tool_calls, stop_reason=stop_reason)

    def _to_gemini_contents(self, messages: list[dict]) -> list:
        """Collapses the orchestrator's simple {user, assistant, tool}
        protocol into Gemini's Content list — Gemini has no separate
        'tool' role: a function result becomes a function_response Part
        on a user-role turn, and an assistant tool request becomes a
        function_call Part on a model-role turn."""
        from google.genai import types

        contents = []
        for m in messages:
            role = m.get("role")
            if role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=m["content"])]))
            elif role == "assistant":
                parts = []
                if m.get("content"):
                    parts.append(types.Part(text=m["content"]))
                for call in m.get("tool_calls") or []:
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=call["name"], args=call["arguments"], id=call.get("id")
                            )
                        )
                    )
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
            elif role == "tool":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=m.get("name", ""),
                                    id=m.get("tool_call_id"),
                                    response={"result": m.get("content")},
                                )
                            )
                        ],
                    )
                )
        return contents
