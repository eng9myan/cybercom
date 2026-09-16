"""
Automated teacher administrative tools (capability #2): lesson plans, rubrics,
and differentiated tasks — all grounded in retrieved ACARA curriculum and all
created as `pending_review` GeneratedArtifacts (mandatory human-in-the-loop).

Each generator produces real, structured content deterministically from the
curriculum (so it works and is testable without an LLM). When `CYED_LLM_ENABLED`
is set, `llm.generate` may enrich the draft; the teacher still approves it.
"""

from products.cyed.ai_agents import acara_v9, llm
from products.cyed.ai_agents.models import AgentDefinition, GeneratedArtifact
from products.cyed.ai_agents.retrieval import retrieve_outcomes


class NoGroundingError(Exception):
    """No ACARA outcome matched — refuse to generate ungrounded material."""


class AgentNotProvisioned(Exception):
    """The agent definition is not registered for this tenant."""


def _agent(tenant_id, key):
    agent = AgentDefinition.objects.filter(tenant_id=tenant_id, key=key, is_active=True).first()
    if agent is None:
        raise AgentNotProvisioned(f"Agent '{key}' is not provisioned for this tenant.")
    return agent


def _short(text, n=90):
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _context(outcomes):
    return "\n".join(
        f"[{o.code}] {o.learning_area} Y{o.year_level} {o.strand}: {o.content_description}"
        for o in outcomes
    )


def generate_lesson_plan(*, tenant_id, topic, year_level=None, learning_area=None, subject="", generated_by=""):
    agent = _agent(tenant_id, "cyed.lesson_planner")
    outcomes = retrieve_outcomes(tenant_id, topic, year_level=year_level, learning_area=learning_area)
    if not outcomes:
        raise NoGroundingError("No matching curriculum outcome for this topic/year.")
    codes = [o.code for o in outcomes]

    content = {
        "topic": topic,
        "year_level": year_level,
        "learning_objectives": [
            f"[{o.code}] {o.content_description or o.strand or o.learning_area}" for o in outcomes
        ],
        "lesson_sequence": [
            {"phase": "Warm-up", "minutes": 10, "activity": f"Activate prior knowledge on {topic}."},
            {"phase": "Explicit teaching", "minutes": 15,
             "activity": f"Teach {topic}, aligned to {codes[0]}."},
            {"phase": "Guided practice", "minutes": 15,
             "activity": "Worked examples, then paired practice with feedback."},
            {"phase": "Independent practice", "minutes": 15,
             "activity": "Differentiated task set (support / core / extension)."},
            {"phase": "Review", "minutes": 5, "activity": "Exit ticket checking the objective."},
        ],
        "assessment": f"Formative exit ticket mapped to {codes[0]}.",
        "differentiation": [
            "Support: scaffolded steps and worked examples",
            "Core: standard task",
            "Extension: open-ended application problem",
            "EAL/D: pre-teach vocabulary, provide visuals and sentence starters",
        ],
        "resources": [],
        "curriculum_codes": codes,
        # ACARA v9 three-dimensional design:
        "general_capabilities": acara_v9.general_capabilities_for(outcomes[0].learning_area),
        "cross_curriculum_priorities": acara_v9.CROSS_CURRICULUM_PRIORITIES,
        "framework": "ACARA v9",
        "disclaimer": acara_v9.HITL_DISCLAIMER,
    }

    enriched = llm.generate(question=f"Lesson plan: {topic}", context=_context(outcomes),
                            model_name=agent.model_name)
    if enriched:
        content["llm_notes"] = enriched

    return GeneratedArtifact.objects.create(
        tenant_id=tenant_id, agent=agent, artifact_type="lesson_plan",
        title=f"{topic} — Year {year_level}" if year_level is not None else topic,
        subject=subject or outcomes[0].learning_area, year_level=year_level,
        curriculum_codes=",".join(codes), content=content,
        status="pending_review", generated_by=generated_by, llm_generated=bool(enriched),
    )


def generate_rubric(*, tenant_id, assessment_title, year_level=None, learning_area=None, generated_by=""):
    agent = _agent(tenant_id, "cyed.rubric")
    outcomes = retrieve_outcomes(tenant_id, assessment_title, year_level=year_level,
                                 learning_area=learning_area)
    if not outcomes:
        raise NoGroundingError("No matching curriculum outcome for this assessment.")
    codes = [o.code for o in outcomes]

    criteria = []
    for o in outcomes:
        base = _short(o.content_description or o.strand or o.learning_area)
        criteria.append({
            "code": o.code,
            "criterion": f"{o.strand or o.learning_area}: {base}",
            "levels": {
                "A": f"Comprehensive, accurate command of {base}",
                "B": f"Thorough understanding of {base}",
                "C": f"Sound, satisfactory understanding of {base}",
                "D": f"Basic, partial understanding of {base}",
                "E": f"Elementary, minimal understanding of {base}",
            },
        })

    content = {
        "assessment": assessment_title,
        "scale": "A–E (Australian Curriculum achievement standards)",
        "criteria": criteria,
        "curriculum_codes": codes,
        "framework": "ACARA v9",
        "disclaimer": acara_v9.HITL_DISCLAIMER,
    }
    return GeneratedArtifact.objects.create(
        tenant_id=tenant_id, agent=agent, artifact_type="rubric",
        title=f"Rubric — {assessment_title}", year_level=year_level,
        subject=outcomes[0].learning_area, curriculum_codes=",".join(codes),
        content=content, status="pending_review", generated_by=generated_by,
    )


def generate_differentiated_task(*, tenant_id, topic, year_level=None, learning_area=None,
                                 student_id=None, generated_by=""):
    agent = _agent(tenant_id, "cyed.differentiator")
    outcomes = retrieve_outcomes(tenant_id, topic, year_level=year_level, learning_area=learning_area)
    if not outcomes:
        raise NoGroundingError("No matching curriculum outcome for this topic.")
    o = outcomes[0]
    base = _short(o.content_description or o.strand or o.learning_area, 120)
    codes = [x.code for x in outcomes]

    content = {
        "outcome": o.code,
        "tiers": {
            "support": f"Scaffolded: {base} — with a worked example and sentence starters.",
            "core": f"Standard: {base}.",
            "extension": f"Challenge: apply {base} to an open-ended, real-world problem.",
        },
        "eald_scaffold": "Pre-teach key vocabulary; provide a bilingual glossary; use visuals.",
        "curriculum_codes": codes,
        "general_capabilities": acara_v9.general_capabilities_for(o.learning_area),
        "framework": "ACARA v9",
        "disclaimer": acara_v9.HITL_DISCLAIMER,
    }

    applied = []
    if student_id:
        from products.cyed.wellbeing.models import LearnerProfile

        profile = LearnerProfile.objects.filter(tenant_id=tenant_id, student_id=student_id).first()
        if profile:
            if profile.eald_level:
                applied.append(f"eald:{profile.eald_level}")
                if profile.first_language:
                    content["eald_scaffold"] += f" Offer first-language ({profile.first_language}) support."
            if profile.is_neurodivergent:
                applied.append("chunked")
                content["tiers"]["support"] += " Break the task into 3 smaller, checkable steps."
            if profile.accommodations:
                content["accommodations"] = profile.accommodations
    content["applied_adaptations"] = applied

    return GeneratedArtifact.objects.create(
        tenant_id=tenant_id, agent=agent, artifact_type="differentiated_task",
        title=f"Differentiated task — {topic}", year_level=year_level,
        subject=o.learning_area, curriculum_codes=",".join(codes),
        content=content, status="pending_review", generated_by=generated_by,
    )
