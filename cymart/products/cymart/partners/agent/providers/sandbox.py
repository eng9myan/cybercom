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
from ..tools import MAX_GUESTS, cart_from_transcript, items_seen, party_from_transcript
from . import scope
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
        "party_set": "Got it: you plus {n} guest(s). Your guests aren't checked against your plan{allergy_part}. What would you like to order?",
        "party_allergies": ", only the allergies you named ({allergies})",
        "party_no_allergies": ", and I have no allergies for them, so tell me if any of them has one",
        "added_both": "Added {name} for you and {qty}× for your guests. Say “confirm” to place the order, or keep browsing.",
        "added_me_only": "Added {name} for you only; I did not add the guests' portions.",
        "guests_refused": "I couldn't add {name} for your guests: {reason}",
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
        "party_set": "تمام: أنت و{n} ضيف/ضيوف. ضيوفك لا يُفحصون وفق خطتك{allergy_part}. ماذا تريد أن تطلب؟",
        "party_allergies": "، فقط الحساسيات التي ذكرتها ({allergies})",
        "party_no_allergies": "، ولا توجد حساسيات مذكورة لهم، فأخبرني إن كان لأحدهم حساسية",
        "added_both": "تمت إضافة {name} لك و{qty}× لضيوفك. قل «تأكيد» لإتمام الطلب، أو واصل التصفح.",
        "added_me_only": "تمت إضافة {name} لك فقط؛ لم أضف حصص الضيوف.",
        "guests_refused": "لا يمكنني إضافة {name} لضيوفك: {reason}",
    },
}


_NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "واحد": 1, "اثنان": 2, "اثنين": 2, "ثلاثه": 3, "ثلاث": 3, "اربعه": 4, "اربع": 4, "خمسه": 5, "خمس": 5}
_EN_N = r"(\d+|one|two|three|four|five|six|seven|eight)"
_AR_N = r"(\d+|واحد|اثنان|اثنين|ثلاثه|ثلاث|اربعه|اربع|خمسه|خمس)"
_GROUP_PATTERNS = [
    re.compile(rf"\bfor\s+me\s+and\s+{_EN_N}\s*(?:friends?|guests?|others?|people|persons?)\b"),
    re.compile(rf"\b{_EN_N}\s+of\s+(?:them|us)\b[^.,;]*?\b(?:not|no|without|aren't|isn't|don't|dont|doesn't)\b[^.,;]*"),
    re.compile(rf"\b{_EN_N}\s+(?:friends?|guests?|others?)\b"),
    re.compile(rf"(?:لي\s+و)?\s*{_AR_N}\s+منهم\s+(?:ليس|بدون|لا|ما|مو)[^.,;،]*"),
    re.compile(rf"{_AR_N}\s*(?:اصدقاء|اصحاب|ضيوف)"),
    re.compile(r"(?:لي\s+)?ول?(صديقين|صديقان)"),
]
_ALLERGY = [re.compile(r"\ballerg\w*\s+(?:to|of|from)\s+([^.;?!]+)"), re.compile(r"حساسيه\s+(?:من|ل)\s*([^.;?!]+)")]
GROUP_FILLERS = set("full meal meals person persons people them us of not no without plan from on in are is and also friends friend "
                    "guests guest allergic allergy to dont don't aren't isn't have has do does me my ordering order "
                    "كامله كامل اشخاص شخص منهم لديهم خطه خطتي عندهم وجبات لشخصين".split())


def _num(tok: str) -> int:
    return int(tok) if tok.isdigit() else _NUMW.get(tok, 0)


def parse_party(text: str):
    """(guests, guest_allergies, text with the group phrases removed) if the customer is ordering for people who
    have no plan, else None. Deliberately narrow: an unclear sentence is not guessed at."""
    low = text.lower().replace("’", "'")
    low = normalise(low) if re.search("[؀-ۿ]", low) else low
    guests = 0
    for i, pat in enumerate(_GROUP_PATTERNS):
        m = pat.search(low)
        if m:
            guests = 2 if i == 5 else _num(m.group(1))
            low = low[:m.start()] + " " + low[m.end():]
            break
    if guests < 1:
        return None
    allergies: list[str] = []
    for pat in _ALLERGY:
        m = pat.search(low)
        if m:
            allergies = [a.strip() for a in re.split(r",|،|\band\b|&|\s+و", m.group(1)) if a.strip()][:10]
            low = low[:m.start()] + " " + low[m.end():]
            break
    return min(guests, MAX_GUESTS), allergies, low


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
        cleaned = scope.clean(text)
        norm = cleaned or normalise(text)
        words = norm.split()
        ranked_now = self._last_ranked(messages)
        has_cart = bool(cart_from_transcript(messages))
        # 0) ordering for people who have no plan comes first (the sentence may also mention an allergy of theirs)
        party = parse_party(text)
        if party is not None and not scope.INJECTION.search(text.lower()):
            guests, allergies, _ = party
            args = {"guests": guests, **({"guest_allergies": allergies} if allergies else {})}
            return Completion(tool_calls=[ToolCall("set_party", args)])
        # 1) everything that is not "find me food": the scripted answers (see scope.py)
        kind = scope.classify(lang, norm, text, has_cart, ranked_now)
        if kind == "plan_q":
            return Completion(tool_calls=[ToolCall("plan_summary", {})])
        if kind:
            ar = lang == "ar" or bool(re.search("[؀-ۿ]", text))
            return Completion(text=scope.R["ar" if ar else lang][kind])
        # 2) quantities: "make it 3", "2 of the first", "double"
        if ranked_now and re.fullmatch(r"\d+", norm) and int(norm) > 20:
            return Completion(text=scope.R[lang]["qty_limit"])
        q = scope.quantity(norm, ranked_now)
        if q is not None and "add_to_cart" in offered:
            idx, n = q
            if n > 20:
                return Completion(text=scope.R[lang]["qty_limit"])
            guests, _ = party_from_transcript(messages)
            args = {"item_id": str(ranked_now[idx]["item_id"]), "quantity": n, **({"for_diner": "me"} if guests else {})}
            return Completion(tool_calls=[ToolCall("add_to_cart", args)])
        if norm in CANCEL or scope.is_cancel(norm):
            return Completion(text=s["cancelled"])
        if norm in CONFIRM or " ".join(words[:2]) in CONFIRM or scope.is_confirm(norm):
            if not cart_from_transcript(messages):
                return Completion(text=s["cart_empty"])
            if "checkout" in offered:
                return Completion(tool_calls=[ToolCall("checkout", {})])
        if (scope.is_cart_view(norm) or "cart" in words or normalise("السلة") in words or normalise("سلتي") in words) and "view_cart" in offered:
            return Completion(tool_calls=[ToolCall("view_cart", {})])

        party = parse_party(text)
        if party is not None:
            guests, allergies, _ = party
            args = {"guests": guests, **({"guest_allergies": allergies} if allergies else {})}
            return Completion(tool_calls=[ToolCall("set_party", args)])

        ranked = self._last_ranked(messages)
        choice = self._choice(norm, words, ranked)
        if choice is None and ranked:
            k = scope.choice_index(norm, len(ranked))
            choice = str(ranked[k]["item_id"]) if k is not None else None
        if choice is not None:
            if "add_to_cart" in offered:
                guests, _ = party_from_transcript(messages)
                args = {"item_id": choice, "quantity": 1, **({"for_diner": "me"} if guests else {})}
                return Completion(tool_calls=[ToolCall("add_to_cart", args)])
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

        if name == "plan_summary":
            return Completion(text=scope.plan_text(lang, p))

        if name == "set_party":
            guests, allergies = party_from_transcript(messages)
            if not guests:
                return Completion(text=s["ask"])
            user = next((m["content"] for m in reversed(messages) if m.get("role") == "user" and isinstance(m.get("content"), str)), "")
            parsed = parse_party(user)
            rest = parsed[2] if parsed else user
            fillers = FILLERS["en"] | FILLERS[lang] | GROUP_FILLERS | {normalise(w) for w in GROUP_FILLERS}
            query = " ".join(w for w in rest.replace("،", " ").split()
                             if normalise(w) not in fillers and not w.isdigit() and normalise(w).lstrip("ل") not in _NUMW).strip(" ?!.,")
            if query:
                return Completion(tool_calls=[ToolCall("search_menu", {"query": query[:200], "limit": 20})])
            part = s["party_allergies"].format(allergies=", ".join(allergies)) if allergies else s["party_no_allergies"]
            return Completion(text=s["party_set"].format(n=guests, allergy_part=part))

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
            diner = call_args.get("for_diner")
            if p.get("ok") is True:
                if diner == "me":
                    guests, _ = party_from_transcript(messages)
                    if guests:   # the same dish for the guests, in the same turn
                        return Completion(tool_calls=[ToolCall("add_to_cart", {"item_id": call_args["item_id"], "quantity": guests, "for_diner": "guests"})])
                if diner == "guests":
                    return Completion(text=s["added_both"].format(name=label, qty=call_args.get("quantity", 1)))
                return Completion(text=s["added"].format(name=label))
            if p.get("error") == "customer_declined":
                return Completion(text=s["added_me_only"].format(name=label) if diner == "guests" else s["declined"])
            reason = p.get("message") or p.get("error", "")
            return Completion(text=(s["guests_refused"] if diner == "guests" else s["refused"]).format(name=label, reason=reason))

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
