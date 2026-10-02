"""Deterministic stand-in for a language model: keyword rules, no network, no key.

It exists so the whole ordering loop (search -> rank -> choose -> kitchen
requirements -> cart -> confirmed checkout) can be run, tested and demoed without an
LLM. It is NOT natural-language understanding: it recognises a search phrase, a
choice ("1", "the second", an item name), a confirmation and a cancel, in English
and Arabic. A real model is a drop-in replacement (see providers/claude.py).
"""

import json
import re

from ...i18n import normalise, t
from ..tools import cart_from_transcript, items_seen
from .base import Completion, CompletionProvider, ToolCall

FILLERS = {
    "en": set("i want to order get give me show find a an some please can you would like something with the for my "
              "need looking look eat have lets let's i'd i'll hungry food some".split()),
    "ar": {normalise(w) for w in "اريد أريد ابغى ابي بدي عايز عاوز اطلب أطلب اعطني أعطني ممكن لو سمحت من فضلك وجبة شيء اي أي".split()},
}
CONFIRM = {normalise(w) for w in "yes yep confirm ok okay sure go ahead place order place it checkout نعم اجل أجل تمام موافق اكد أكد أكّد تأكيد تاكيد".split()}
CANCEL = {normalise(w) for w in "no nope cancel stop not now لا الغاء إلغاء توقف".split()}
ORDINALS = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    normalise("الاول"): 1, normalise("الأول"): 1, normalise("الثاني"): 2, normalise("الثالث"): 3,
}

MEAL_NAMES = {
    "en": {"breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner", "snack": "a snack"},
    "ar": {"breakfast": "الإفطار", "lunch": "الغداء", "dinner": "العشاء", "snack": "وجبة خفيفة"},
}

S = {
    "en": {
        "ask": "What would you like to eat? I'll only show options that fit your plan.",
        "none": "Nothing in those results fits your plan{why}. Try another dish or a broader search.",
        "header": "Here is what fits your plan:",
        "line": "{n}. {name}{where} — {summary}{flag}",
        "flag_warn": " (note: partly outside your plan)",
        "with_changes": " [made for you: {changes}]",
        "chg_remove": "no {ingredient}",
        "chg_sub": "{replacement} instead of {ingredient}",
        "hidden": "{k} other option(s) were hidden because they don't fit your plan.",
        "pick": "Which one would you like? Say the number or the name.",
        "added": "Added {name} to your cart. Say “confirm” to place the order, or keep browsing.",
        "refused": "I can't add {name}: {reason}",
        "placed": "Your order is placed.",
        "cart_empty": "Your cart is empty. What would you like to order?",
        "declined": "No problem — I haven't changed anything. What else can I find?",
        "cart": "Your cart: {lines}.",
        "error": "Something went wrong with that step: {error}",
        "unknown_choice": "I couldn't tell which option you meant. Say the number or the name.",
        "nothing_to_pick": "Tell me what you'd like first and I'll find options that fit your plan.",
        "cancelled": "Okay, cancelled. What else can I help with?",
    },
    "ar": {
        "ask": "ماذا تود أن تأكل؟ سأعرض لك فقط الخيارات المناسبة لخطتك.",
        "none": "لا يوجد في هذه النتائج ما يناسب خطتك{why}. جرّب صنفًا آخر أو بحثًا أوسع.",
        "header": "هذه الخيارات المناسبة لخطتك:",
        "line": "{n}. {name}{where} — {summary}{flag}",
        "flag_warn": " (تنبيه: خارج خطتك جزئيًا)",
        "with_changes": " [يُحضَّر لك: {changes}]",
        "chg_remove": "بدون {ingredient}",
        "chg_sub": "{replacement} بدلًا من {ingredient}",
        "hidden": "تم إخفاء {k} خيار(ات) أخرى لأنها لا تناسب خطتك.",
        "pick": "أي واحد تريد؟ اذكر الرقم أو الاسم.",
        "added": "تمت إضافة {name} إلى سلتك. قل «تأكيد» لإتمام الطلب، أو واصل التصفح.",
        "refused": "لا يمكنني إضافة {name}: {reason}",
        "placed": "تم إرسال طلبك.",
        "cart_empty": "سلتك فارغة. ماذا تريد أن تطلب؟",
        "declined": "لا مشكلة — لم أغيّر شيئًا. ماذا أبحث لك أيضًا؟",
        "cart": "سلتك: {lines}.",
        "error": "حدث خطأ في هذه الخطوة: {error}",
        "unknown_choice": "لم أفهم أي خيار تقصد. اذكر الرقم أو الاسم.",
        "nothing_to_pick": "أخبرني أولًا ماذا تريد وسأجد لك خيارات مناسبة لخطتك.",
        "cancelled": "حسنًا، تم الإلغاء. بماذا أساعدك أيضًا؟",
    },
}


def _payload(m):
    c = m.get("content")
    if isinstance(c, str):
        try:
            return json.loads(c)
        except ValueError:
            return c
    return c


class SandboxCompletionProvider(CompletionProvider):
    def complete(self, system, messages, tools, language="en") -> Completion:
        lang = language if language in S else "en"
        offered = {t["name"] for t in tools}
        last = messages[-1] if messages else {"role": "user", "content": ""}
        if last["role"] == "tool":
            return self._after_tool(lang, messages, last)
        if last["role"] == "user":
            return self._on_user(lang, messages, last["content"], offered)
        return Completion(text=S[lang]["ask"])

    # ── reacting to the customer ────────────────────────────────────────────
    def _on_user(self, lang, messages, text, offered) -> Completion:
        s = S[lang]
        norm = normalise(text)
        words = norm.split()
        if norm in CANCEL:
            return Completion(text=s["cancelled"])
        if norm in CONFIRM or " ".join(words[:2]) in CONFIRM:
            if not cart_from_transcript(messages):
                return Completion(text=s["cart_empty"])
            if "checkout" in offered:
                return Completion(tool_calls=[ToolCall("checkout", {})])
        if ("cart" in words or normalise("السلة") in words or normalise("سلتي") in words) and "view_cart" in offered:
            return Completion(tool_calls=[ToolCall("view_cart", {})])

        ranked = self._last_ranked(messages)
        choice = self._choice(norm, words, ranked)
        if choice is not None:
            if "add_to_cart" in offered:
                return Completion(tool_calls=[ToolCall("add_to_cart", {"item_id": choice, "quantity": 1})])
        elif ranked and re.fullmatch(r"\s*(number|option|رقم)?\s*\d+\s*", norm):
            return Completion(text=s["unknown_choice"])

        fillers = FILLERS[lang] | FILLERS["en"]
        query = " ".join(w for w in text.replace("،", " ").split() if normalise(w) not in fillers).strip(" ?!.,")
        if not query:
            return Completion(text=s["ask"] if not ranked else s["unknown_choice"])
        if "search_menu" in offered:
            return Completion(tool_calls=[ToolCall("search_menu", {"query": query[:200], "limit": 20})])
        return Completion(text=s["ask"])

    @staticmethod
    def _last_ranked(messages) -> list[dict]:
        """The options most recently shown to the customer (the latest rank_for_plan result)."""
        for m in reversed(messages):
            if m.get("role") == "tool" and m.get("name") == "rank_for_plan":
                p = _payload(m)
                return p.get("ranked", []) if isinstance(p, dict) else []
        return []

    @staticmethod
    def _choice(norm, words, ranked):
        if not ranked:
            return None
        m = re.fullmatch(r"\s*(?:number|option|رقم)?\s*(\d+)\s*", norm)
        if m and 1 <= int(m.group(1)) <= len(ranked):
            return str(ranked[int(m.group(1)) - 1]["item_id"])
        for w in words:
            if w in ORDINALS and ORDINALS[w] <= len(ranked):
                return str(ranked[ORDINALS[w] - 1]["item_id"])
        for r in ranked:
            name = normalise(r.get("name") or "")
            if name and name in norm:
                return str(r["item_id"])
        return None

    # ── reacting to a tool result ───────────────────────────────────────────
    def _after_tool(self, lang, messages, last) -> Completion:
        s = S[lang]
        p = _payload(last)
        name = last.get("name")
        seen, _ = items_seen(messages)
        if not isinstance(p, dict):
            return Completion(text=s["error"].format(error=str(p)[:100]))

        if name == "search_menu":
            if p.get("ok") is False:
                return Completion(text=s["error"].format(error=p.get("error", "")))
            return Completion(tool_calls=[ToolCall("rank_for_plan", {"limit": 5})])

        if name == "rank_for_plan":
            ranked, hidden = p.get("ranked", []), p.get("counts", {}).get("excluded", 0)
            if not ranked:
                why = f" ({hidden} hidden by your plan)" if hidden else ""
                return Completion(text=s["none"].format(why=why))
            lines = [self._header(lang, messages, s)]
            for r in ranked[:3]:
                where = f" ({r['restaurant']})" if r.get("restaurant") else ""
                flag = s["flag_warn"] if r.get("severity") == "warn" else ""
                changes = ", ".join(
                    s["chg_sub"].format(replacement=c["replacement"], ingredient=c["ingredient"]) if c["type"] == "substitute"
                    else s["chg_remove"].format(ingredient=c["ingredient"])
                    for c in r.get("changes") or [])
                flag += s["with_changes"].format(changes=changes) if changes else ""
                lines.append(s["line"].format(n=r["rank"], name=r.get("name") or r["item_id"], where=where,
                                              summary=r.get("summary", ""), flag=flag))
            if hidden:
                lines.append(s["hidden"].format(k=hidden))
            lines.append(s["pick"])
            return Completion(text="\n".join(lines))

        if name == "add_to_cart":
            call_args = self._args_of(messages, last)
            item = seen.get(str(call_args.get("item_id")), {})
            label = item.get("name") or str(call_args.get("item_id"))
            if p.get("ok") is True:
                return Completion(text=s["added"].format(name=label))
            if p.get("error") == "customer_declined":
                return Completion(text=s["declined"])
            return Completion(text=s["refused"].format(name=label, reason=p.get("message") or p.get("error", "")))

        if name == "view_cart":
            items = p.get("items") or []
            if not items:
                return Completion(text=s["cart_empty"])
            lines = ", ".join(f"{i.get('quantity', 1)}× {(seen.get(str(i['item_id'])) or {}).get('name') or i['item_id']}" for i in items)
            return Completion(text=s["cart"].format(lines=lines))

        if name == "checkout":
            if p.get("ok") is True:
                return Completion(text=s["placed"])
            if p.get("error") == "customer_declined":
                return Completion(text=s["declined"])
            return Completion(text=p.get("message") or s["error"].format(error=p.get("error", "")))

        return Completion(text=s["error"].format(error=p.get("error", name or "")))

    @staticmethod
    def _header(lang, messages, s) -> str:
        first = messages[0]["content"] if messages and isinstance(messages[0].get("content"), str) else ""
        m = re.match(r"\[meal_time:(\w+)\]", first)
        if not m:
            return s["header"]
        names = MEAL_NAMES[lang]
        return t(lang, "meal_header", meal=names.get(m.group(1), m.group(1)))

    @staticmethod
    def _args_of(messages, tool_msg) -> dict:
        tid = tool_msg.get("tool_call_id")
        for m in reversed(messages):
            for c in m.get("tool_calls") or []:
                if c.get("id") == tid:
                    return c.get("arguments") or {}
        return {}
