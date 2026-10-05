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


MAX_GUESTS = 8
ME, GUESTS = "me", "guests"

_DINER = {"type": "string", "maxLength": 10}

REGISTRY: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec("plan_summary",
                 "The customer's own plan: allergies, diet rules, calories left, strictness. Use it to restate the plan; never guess it.",
                 _obj({}), "server"),
        ToolSpec("set_party",
                 "Use when the customer is ordering for other people too (friends or family who have no plan here). "
                 "guests = how many people besides the customer; 0 means just the customer. guest_allergies = allergies the customer "
                 "SAID the guests have (applied to every guest); never invent any. Guests are not checked against the customer's plan; "
                 "only the allergies named here are applied. Returns the diner ids to use as for_diner: 'me' and 'guests'.",
                 _obj({"guests": {"type": "integer", "minimum": 0, "maximum": MAX_GUESTS},
                       "guest_allergies": {"type": "array", "items": {"type": "string", "maxLength": 40}, "maxItems": 10}},
                      ["guests"]), "server"),
        ToolSpec("rank_for_plan",
                 "Filter and rank the items from the most recent search_menu result against the customer's plan "
                 "(or, with for_diner='guests', against the guests' stated allergies). "
                 "Returns only items that fit, best first, and how many were hidden and why. Call it after every search.",
                 _obj({"limit": {"type": "integer", "minimum": 1, "maximum": 10}, "for_diner": _DINER}), "server"),
        ToolSpec("check_item",
                 "Check one item the customer asked about (an item_id from a search result) against their plan "
                 "(or the guests' stated allergies with for_diner='guests').",
                 _obj({"item_id": {"type": "string"}, "for_diner": _DINER}, ["item_id"]), "server"),
        ToolSpec("prepare_item",
                 "Preview the kitchen requirements for one item (an item_id from a search result): changes such as "
                 "'no tomato' or 'gluten-free bread' that this customer needs (or the guests, with for_diner='guests').",
                 _obj({"item_id": {"type": "string"}, "for_diner": _DINER}, ["item_id"]), "server"),
        ToolSpec("search_menu",
                 "Search the platform's menu for food or grocery items by name, cuisine or category. Returns items with nutrition data.",
                 _obj({"query": {"type": "string", "maxLength": 200}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                      ["query"]), "client"),
        ToolSpec("add_to_cart",
                 "Add an item from a search result to the customer's cart. Diet Shield checks it against the plan first and "
                 "attaches the kitchen requirements; it may be refused or need the customer's confirmation. "
                 "When the customer ordered for guests (set_party), for_diner is required: 'me' for the customer's own portion, "
                 "'guests' for the guests' portions (quantity = how many portions for the guests).",
                 _obj({"item_id": {"type": "string"}, "quantity": {"type": "integer", "minimum": 1, "maximum": MAX_QUANTITY},
                       "for_diner": _DINER}, ["item_id"]), "client"),
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
        elif schema["type"] == "array":
            if not isinstance(value, list) or len(value) > schema["maxItems"]:
                raise ToolRefused("bad_arguments", f"'{key}' must be a list of at most {schema['maxItems']} items.")
            cleaned = []
            for v in value:
                if not isinstance(v, str) or not v.strip() or len(v) > schema["items"]["maxLength"]:
                    raise ToolRefused("bad_arguments", f"'{key}' must contain short, non-empty text.")
                cleaned.append(v.strip())
            out[key] = cleaned
    return out


# ── the party (who is eating): derived from the transcript, never stored ──────────
def party_from_transcript(messages: list[dict]) -> tuple[int, list[str]]:
    """(number of guests, the allergies the customer named for them). The most recent valid set_party
    call in the transcript wins; no call means the customer is ordering only for themselves."""
    guests, allergies = 0, []
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for c in m.get("tool_calls") or []:
            if c.get("name") != "set_party":
                continue
            try:
                a = validate_arguments("set_party", c.get("arguments") or {})
            except ToolRefused:
                continue
            guests, allergies = a["guests"], a.get("guest_allergies") or []
    return guests, allergies


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
    """The cart by item only (all diners added together)."""
    out: dict[str, int] = {}
    for (iid, _), qty in cart_lines(messages).items():
        out[iid] = out.get(iid, 0) + qty
    return out


def _diner_of(a: dict) -> str:
    return GUESTS if a.get("for_diner") == GUESTS else ME


def cart_lines(messages: list[dict]) -> dict[tuple[str, str], int]:
    """The cart as the platform confirmed it, one line per (item, diner): every add_to_cart the platform
    answered ok, unless a later view_cart result replaced it."""
    cart: dict[tuple[str, str], int] = {}
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
                key = (str(a.get("item_id")), _diner_of(a))
                cart[key] = cart.get(key, 0) + int(a.get("quantity") or 1)
            elif m.get("name") == "view_cart" and isinstance(payload, dict) and isinstance(payload.get("items"), list):
                cart = {(str(i["item_id"]), _diner_of(i)): int(i.get("quantity") or 1)
                        for i in payload["items"] if isinstance(i, dict) and "item_id" in i}
            elif m.get("name") == "checkout" and isinstance(payload, dict) and payload.get("ok") is True:
                cart = {}
    return cart
