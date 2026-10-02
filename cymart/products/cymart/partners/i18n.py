"""English and Arabic wording for everything Diet Shield writes in prose.

Codes (``allergen_conflict``, ``remove``, ``cannot_make_safe`` ...) never change
between languages; only the human-readable ``reason`` / ``summary`` / ``text`` /
``vendor_note`` fields do. Names that come from the partner (ingredients,
allergens, item ids, diet-rule codes) are echoed exactly as sent, so a vendor
that sends Arabic ingredient names gets an Arabic ticket end to end.

Arabic wording was drafted for clarity and needs review by a native speaker
before it is shown to customers or kitchens.
"""

from __future__ import annotations

import re

LANGUAGES = ("en", "ar")

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "ok": "Fits the plan.",
        "allergen_conflict": "Contains allergen(s): {matched}.",
        "ingredients_unknown": "Ingredients unknown — allergy check could not be completed.",
        "regime_blocked_ingredient": "{regime}: contains {matched}.",
        "regime_carb_limit": "{regime}: carbs over limit.",
        "regime_not_compatible": "Not marked {regime}-compatible.",
        "calorie_budget_exceeded": "{calories} kcal exceeds remaining budget.",
        # kitchen instructions
        "alert_text": "Customer allergy: {allergens}. Use clean utensils and surfaces to avoid cross-contact.",
        "alert_note": "ALLERGY: {allergens_u}. Use clean utensils and surfaces to avoid cross-contact.",
        "why_allergy": "Customer allergy: {ingredient}.",
        "why_allergy_multi": "Customer allergy: {allergens}.",
        "why_regime": "Diet rule ({regime}): {ingredient} not allowed.",
        "verify_text": "Ingredient list unknown. Confirm the item is free of the customer's allergens before preparing.",
        "note_remove": "NO {ingredient_u} ({reason})",
        "note_substitute": "USE {replacement_u} instead of {ingredient} ({reason})",
        "note_cannot": "CANNOT MAKE: {ingredient} cannot be removed or replaced ({reason})",
        "head_ok": "{item}: prepare as listed",
        "head_ok_with_changes": "{item}: prepare with the changes below",
        "head_needs_vendor_confirmation": "{item}: confirm ingredients before preparing",
        "head_cannot_make_safe": "{item}: cannot be made to fit this customer's plan",
        # ordering agent
        "ag_unknown_item": "That item isn't in the results I have. Let me search for it first.",
        "ag_unknown_tool": "That action isn't available here.",
        "ag_bad_args": "That request wasn't valid: {detail}",
        "ag_cart_empty": "The cart is empty.",
        "ag_step_limit": "I couldn't finish that. Could you say again what you'd like?",
        "ag_confirm_add": "Please confirm adding {name}.{changes}{warning}",
        "ag_changes": " The kitchen will be asked to: {changes}.",
        "ag_warning": " Note: {reason}",
        "ag_confirm_checkout": "Please confirm your order: {lines}. About {total} kcal in total.{warning}",
        "ag_line": "{qty}× {name}",
        # plan setup, weekly plan, grocery basket
        "plan_pace_capped": "Pace capped at {cap} kg a week (you asked for {pace}); faster is not recommended.",
        "plan_no_deficit": "No calorie deficit is planned during pregnancy or breastfeeding: the target is at least your maintenance level.",
        "plan_floor": "Target raised to the safety minimum of {floor} kcal a day.",
        "plan_medical": "A medical condition affects diet advice: please review this plan with a doctor or dietitian.",
        "plan_disclaimer": "This is a starting plan from standard formulas, not medical advice. Review it with a professional if you have any health condition.",
        "week_nothing_fits": "Nothing available fits your plan for {meal}.",
        "week_note_choose": "These are suggestions. At each meal you choose from the options, and every order is checked against your allergies and diet again.",
        "basket_no_items": "No {category} items are available.",
        "basket_nothing_fits": "No {category} item fits your plan.",
        "basket_note_template": "Weekly servings per food group are a starter template, not dietary advice. Your nutrition team can set them.",
        "meal_header": "It's time for {meal}. Here is what fits your plan:",
        # ranking summaries
        "tag_compatible": "{tags}-compatible",
        "kcal_vs_target": "{calories} kcal vs a {target} kcal target",
        "leaves_kcal": "leaves {left} kcal",
        "carbs_vs_limit": "{carbs} g carbs (limit {limit})",
    },
    "ar": {
        "ok": "يناسب خطتك.",
        "allergen_conflict": "يحتوي على مسبّب(ات) الحساسية: {matched}.",
        "ingredients_unknown": "المكوّنات غير معروفة — تعذّر إكمال فحص الحساسية.",
        "regime_blocked_ingredient": "{regime}: يحتوي على {matched}.",
        "regime_carb_limit": "{regime}: الكربوهيدرات تتجاوز الحد.",
        "regime_not_compatible": "غير مصنَّف كمناسب لنظام {regime}.",
        "calorie_budget_exceeded": "{calories} سعرة حرارية تتجاوز الرصيد المتبقي.",
        "alert_text": "حساسية العميل: {allergens}. استخدم أدوات وأسطحًا نظيفة لتجنّب التلوّث الخلطي.",
        "alert_note": "تنبيه حساسية: {allergens}. استخدم أدوات وأسطحًا نظيفة لتجنّب التلوّث الخلطي.",
        "why_allergy": "حساسية العميل: {ingredient}.",
        "why_allergy_multi": "حساسية العميل: {allergens}.",
        "why_regime": "نظام {regime} الغذائي: {ingredient} غير مسموح.",
        "verify_text": "قائمة المكوّنات غير معروفة. تأكّد من خلوّ الصنف من مسبّبات حساسية العميل قبل التحضير.",
        "note_remove": "بدون {ingredient} — {reason}",
        "note_substitute": "استخدم {replacement} بدلًا من {ingredient} — {reason}",
        "note_cannot": "لا يمكن التحضير: لا يمكن إزالة {ingredient} أو استبداله — {reason}",
        "head_ok": "{item}: حضّر الطلب كما هو",
        "head_ok_with_changes": "{item}: حضّر الطلب مع التعديلات التالية",
        "head_needs_vendor_confirmation": "{item}: تأكّد من المكوّنات قبل التحضير",
        "head_cannot_make_safe": "{item}: لا يمكن تحضيره بما يناسب خطة العميل",
        "ag_unknown_item": "هذا الصنف ليس ضمن النتائج لدي. دعني أبحث عنه أولًا.",
        "ag_unknown_tool": "هذا الإجراء غير متاح هنا.",
        "ag_bad_args": "الطلب غير صالح: {detail}",
        "ag_cart_empty": "السلة فارغة.",
        "ag_step_limit": "لم أتمكن من إكمال ذلك. هل يمكنك إعادة ما تريده؟",
        "ag_confirm_add": "يرجى تأكيد إضافة {name}.{changes}{warning}",
        "ag_changes": " سيُطلب من المطبخ: {changes}.",
        "ag_warning": " تنبيه: {reason}",
        "ag_confirm_checkout": "يرجى تأكيد طلبك: {lines}. المجموع تقريبًا {total} سعرة حرارية.{warning}",
        "ag_line": "{qty}× {name}",
        "plan_pace_capped": "تم تحديد وتيرة التغيير بـ {cap} كغ أسبوعيًا (طلبت {pace})؛ الأسرع غير موصى به.",
        "plan_no_deficit": "لا يوجد عجز في السعرات أثناء الحمل أو الرضاعة: الهدف لا يقل عن مستوى المحافظة على الوزن.",
        "plan_floor": "تم رفع الهدف إلى الحد الأدنى الآمن وهو {floor} سعرة يوميًا.",
        "plan_medical": "حالة صحية تؤثر على النصائح الغذائية: يرجى مراجعة هذه الخطة مع طبيب أو أخصائي تغذية.",
        "plan_disclaimer": "هذه خطة مبدئية مبنية على معادلات معيارية وليست نصيحة طبية. راجعها مع مختص إن كانت لديك أي حالة صحية.",
        "week_nothing_fits": "لا يتوفر ما يناسب خطتك لوجبة {meal}.",
        "week_note_choose": "هذه اقتراحات. في كل وجبة تختار من الخيارات، ويُفحص كل طلب مجددًا وفق حساسيتك ونظامك الغذائي.",
        "basket_no_items": "لا توجد أصناف من فئة {category}.",
        "basket_nothing_fits": "لا يوجد صنف من فئة {category} يناسب خطتك.",
        "basket_note_template": "الحصص الأسبوعية لكل مجموعة غذائية قالب مبدئي وليست نصيحة غذائية. يمكن لفريق التغذية لديكم تحديدها.",
        "meal_header": "حان وقت {meal}. هذه الخيارات المناسبة لخطتك:",
        "tag_compatible": "مناسب لـ {tags}",
        "kcal_vs_target": "{calories} سعرة مقابل هدف {target} سعرة",
        "leaves_kcal": "يتبقى {left} سعرة",
        "carbs_vs_limit": "{carbs} غ كربوهيدرات (الحد {limit})",
    },
}


def t(lang: str, key: str, **params) -> str:
    """Render ``key`` in ``lang``. For every string param ``x`` an upper-cased
    ``x_u`` is also available (used for the English kitchen ticket; a no-op in Arabic)."""
    table = MESSAGES.get(lang) or MESSAGES["en"]
    template = table.get(key) or MESSAGES["en"][key]
    full = dict(params)
    for k, v in params.items():
        if isinstance(v, str):
            full[f"{k}_u"] = v.upper()
    return template.format(**full)


def join_list(lang: str, values) -> str:
    return ("، " if lang == "ar" else ", ").join(str(v) for v in values)


# ── Arabic-aware text normalisation, so matching works however the name was typed ──
_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_ALEF = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و"})


def normalise(value) -> str:
    s = str(value).strip().lower()
    if not s:
        return ""
    s = _DIACRITICS.sub("", s).translate(_ALEF)
    # ta marbuta / ha: treat as the same letter so "فستقة" and "فستقه" match
    s = s.replace("ة", "ه")
    # Strip the definite article (and common one-letter prefixes before it) from each
    # word, so "فول سوداني" is found inside "الفول السوداني". Applied to both sides
    # of every comparison, so it only ever makes matching more inclusive.
    return " ".join(_strip_article(w) for w in s.split())


def _strip_article(word: str) -> str:
    for prefix in ("وال", "بال", "كال", "فال"):
        if word.startswith(prefix) and len(word) > len(prefix) + 1:
            return word[len(prefix):]
    if word.startswith("ال") and len(word) > 3:
        return word[2:]
    return word
