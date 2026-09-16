"""
ACARA v9 framework constants — the three-dimensional design the Teacher AI must
embed: Learning Areas, the 7 General Capabilities, and the 3 Cross-Curriculum
Priorities. Plus Australian-English + human-in-the-loop conventions.
"""

GENERAL_CAPABILITIES = [
    "Literacy",
    "Numeracy",
    "Critical and Creative Thinking",
    "Digital Literacy",
    "Personal and Social Capability",
    "Ethical Understanding",
    "Intercultural Understanding",
]

CROSS_CURRICULUM_PRIORITIES = [
    "Aboriginal and Torres Strait Islander Histories and Cultures",
    "Asia and Australia's Engagement with Asia",
    "Sustainability",
]

HITL_DISCLAIMER = (
    "AI-generated — review and adapt this material for your specific classroom "
    "context before use."
)

# Primary general capabilities most commonly foregrounded per learning area.
_AREA_GC = {
    "mathematics": ["Numeracy", "Critical and Creative Thinking"],
    "english": ["Literacy", "Critical and Creative Thinking"],
    "science": ["Numeracy", "Critical and Creative Thinking", "Digital Literacy"],
    "hass": ["Literacy", "Ethical Understanding", "Intercultural Understanding"],
    "technologies": ["Digital Literacy", "Critical and Creative Thinking"],
    "the arts": ["Critical and Creative Thinking", "Personal and Social Capability"],
    "health and physical education": ["Personal and Social Capability", "Ethical Understanding"],
    "languages": ["Intercultural Understanding", "Literacy"],
}


def general_capabilities_for(learning_area: str) -> list[str]:
    key = (learning_area or "").strip().lower()
    return _AREA_GC.get(key, ["Literacy", "Numeracy", "Critical and Creative Thinking"])
