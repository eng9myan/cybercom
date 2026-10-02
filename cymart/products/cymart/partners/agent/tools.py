"""The agent's tool boundary: a closed, default-deny registry.

Two kinds of tool exist, and nothing else:

  SERVER tools  run inside Diet Shield, on data already in the conversation:
                plan_summary, rank_for_plan, check_item, prepare_item.
                They never take nutrition data from the model.

  CLIENT tools  are carried out by the PLATFORM (talabat's own search, cart and
                checkout). Diet Shield only ever proposes them; the platform runs
                them against its own systems and returns the result. A platform
                lists which ones it supports; any other name is refused.

Whatever a model asks for, a name outside this registry is refused and an
argument that fails validation is refused, before anything is acted on.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

MAX_QUANTITY = 20


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict
    kind: str  # "server" | "client"


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [], "additionalProperties": False}


REGISTRY: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec("plan_summary",
                 "The customer's own plan: allergies, diet rules, calories left, strictness. Use it to restate the plan; never guess it.",
                 _obj({}), "server"),
        ToolSpec("rank_for_plan",
                 "Filter and rank the items from the most recent search_menu result against the customer's plan. "
                 "Returns only items that fit, best first, and how many were hidden and why. Call it after every search.",
                 _obj({"limit": {"type": "integer", "minimum": 1, "maximum": 10}}), "server"),
        ToolSpec("check_item",
                 "Check one item the customer asked about (an item_id from a search result) against their plan.",
                 _obj({"item_id": {"type": "string"}}, ["item_id"]), "server"),
        ToolSpec("prepare_item",
                 "Preview the kitchen requirements for one item (an item_id from a search result): changes such as "
                 "'no tomato' or 'gluten-free bread' that this customer needs.",
                 _obj({"item_id": {"type": "string"}}, ["item_id"]), "server"),
        ToolSpec("search_menu",
                 "Search the platform's menu for food or grocery items by name, cuisine or category. Returns items with nutrition data.",
                 _obj({"query": {"type": "string", "maxLength": 200}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                      ["query"]), "client"),
        ToolSpec("add_to_cart",
                 "Add an item from a search result to the customer's cart. Diet Shield checks it against the plan first and "
                 "attaches the kitchen requirements; it may be refused or need the customer's confirmation.",
                 _obj({"item_id": {"type": "string"}, "quantity": {"type": "integer", "minimum": 1, "maximum": MAX_QUANTITY}},
                      ["item_id"]), "client"),
        ToolSpec("view_cart", "Show what is currently in the customer's cart.", _obj({}), "client"),
        ToolSpec("checkout",
                 "Place the order for the current cart. Always needs the customer's explicit confirmation in the app.",
                 _obj({}), "client"),
    ]
}

SERVER_TOOLS = {n for n, s in REGISTRY.items() if s.kind == "server"}
CLIENT_TOOLS = {n for n, s in REGISTRY.items() if s.kind == "client"}


def specs_for(platform_tools: list[str]) -> list[dict]:
    """The JSON-schema list a model is given: every server tool plus only the
    client tools this platform supports. Nothing else is ever visible to it."""
    allowed = SERVER_TOOLS | (set(platform_tools) & CLIENT_TOOLS)
    return [
        {"name": s.name, "description": s.description, "parameters": s.parameters}
        for s in REGISTRY.values() if s.name in allowed
    ]


class ToolRefused(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


def validate_arguments(name: str, args) -> dict:
    """Strict, hand-rolled check against the registry schema. Raises ToolRefused."""
    spec = REGISTRY.get(name)
    if spec is None:
        raise ToolRefused("unknown_tool", f"'{name}' is not a tool this agent has.")
    if not isinstance(args, dict):
        raise ToolRefused("bad_arguments", "Arguments must be an object.")
    props = spec.parameters["properties"]
    extra = set(args) - set(props)
    if extra:
        raise ToolRefused("bad_arguments", f"Unexpected argument(s): {', '.join(sorted(extra))}.")
    for req in spec.parameters["required"]:
        if req not in args:
            raise ToolRefused("bad_arguments", f"Missing argument '{req}'.")
    out = {}
    for key, value in args.items():
        schema = props[key]
        if schema["type"] == "string":
            if not isinstance(value, str) or not value.strip():
                raise ToolRefused("bad_arguments", f"'{key}' must be a non-empty string.")
            if len(value) > schema.get("maxLength", 200):
                raise ToolRefused("bad_arguments", f"'{key}' is too long.")
            out[key] = value.strip()
        elif schema["type"] == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ToolRefused("bad_arguments", f"'{key}' must be a whole number.")
            if not schema["minimum"] <= value <= schema["maximum"]:
                raise ToolRefused("bad_arguments", f"'{key}' must be between {schema['minimum']} and {schema['maximum']}.")
            out[key] = value
    return out


# ── reading the transcript ────────────────────────────────────────────────────
def _content(m: dict):
    c = m.get("content")
    if isinstance(c, str):
        try:
            return json.loads(c)
        except ValueError:
            return c
    return c


def items_seen(messages: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    """(every item the platform has returned so far keyed by item_id,
    the items of the MOST RECENT search_menu result in order). Item data only
    ever comes from the platform's own tool results, never from the model."""
    seen: dict[str, dict] = {}
    latest: list[dict] = []
    for m in messages:
        if m.get("role") == "tool" and m.get("name") == "search_menu":
            payload = _content(m)
            items = payload.get("items") if isinstance(payload, dict) else None
            if isinstance(items, list):
                latest = [i for i in items if isinstance(i, dict) and i.get("item_id") is not None]
                for i in latest:
                    seen[str(i["item_id"])] = i
    return seen, latest


def unresolved_tool_calls(messages: list[dict]) -> list[dict]:
    """Tool calls on the last assistant message that have no tool result yet."""
    if not messages:
        return []
    last = messages[-1]
    if last.get("role") == "assistant" and last.get("tool_calls"):
        return list(last["tool_calls"])
    return []


def cart_from_transcript(messages: list[dict]) -> dict[str, int]:
    """The cart as the platform confirmed it: every add_to_cart the platform
    answered ok, unless a later view_cart result replaced it."""
    cart: dict[str, int] = {}
    pending: dict[str, dict] = {}
    for m in messages:
        if m.get("role") == "assistant":
            for c in m.get("tool_calls") or []:
                pending[str(c.get("id"))] = c
        elif m.get("role") == "tool":
            payload = _content(m)
            call = pending.get(str(m.get("tool_call_id")))
            if m.get("name") == "add_to_cart" and call and isinstance(payload, dict) and payload.get("ok") is True:
                a = call.get("arguments") or {}
                iid = str(a.get("item_id"))
                cart[iid] = cart.get(iid, 0) + int(a.get("quantity") or 1)
            elif m.get("name") == "view_cart" and isinstance(payload, dict) and isinstance(payload.get("items"), list):
                cart = {str(i["item_id"]): int(i.get("quantity") or 1)
                        for i in payload["items"] if isinstance(i, dict) and "item_id" in i}
            elif m.get("name") == "checkout" and isinstance(payload, dict) and payload.get("ok") is True:
                cart = {}
    return cart
