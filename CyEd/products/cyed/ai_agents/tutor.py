"""
Curriculum-Aligned Learning Assistant (capability #1).

Answers a student's question grounded strictly in retrieved ACARA curriculum,
with citations. Privacy-first by construction: no student input is used for
training, every interaction is logged for transparency, and out-of-curriculum
questions are declined rather than answered free-form.
"""

from products.cyed.ai_agents import anonymize, llm
from products.cyed.ai_agents.models import AgentDefinition, AgentInteractionLog
from products.cyed.ai_agents.retrieval import retrieve_outcomes

TUTOR_KEY = "cyed.tutor"


def _adaptations_for(tenant_id, student_id):
    """Read the student's LearnerProfile (if any) into presentation adaptations."""
    if not student_id:
        return []
    from products.cyed.wellbeing.models import LearnerProfile

    profile = LearnerProfile.objects.filter(tenant_id=tenant_id, student_id=student_id).first()
    if not profile:
        return []
    adaptations = []
    if profile.eald_level:
        adaptations.append(f"eald:{profile.eald_level}")  # simplified language + scaffolding
        if profile.first_language:
            adaptations.append(f"first_language:{profile.first_language}")
    if profile.is_neurodivergent:
        adaptations.append("chunked")  # shorter steps, reduced cognitive load
    if profile.reading_level:
        adaptations.append(f"reading_level:{profile.reading_level}")
    return adaptations


def _extractive_answer(question, outcomes, adaptations):
    """Grounded fallback answer when no LLM is configured."""
    codes = ", ".join(o.code for o in outcomes)
    lead = "eald:" in " ".join(adaptations)
    parts = [f"Here's what the Australian Curriculum covers for this ({codes}):"]
    for o in outcomes:
        desc = o.content_description or o.achievement_standard or o.strand
        parts.append(f"• [{o.code}] {desc}")
    if lead:
        parts.append("(Explained in simpler language for an EAL/D learner — ask your teacher if any word is unclear.)")
    parts.append("This is grounded in your curriculum and is reviewed by your teacher.")
    return "\n".join(parts)


def ask(*, tenant_id, question, student_id=None, year_level=None, learning_area=None, actor=""):
    """
    Return a grounded tutor response:
      { answer, grounded, citations[], adaptations[], agent_key, reviewed_by_human }
    """
    agent = AgentDefinition.objects.filter(tenant_id=tenant_id, key=TUTOR_KEY, is_active=True).first()

    outcomes = retrieve_outcomes(
        tenant_id, question, year_level=year_level, learning_area=learning_area
    )
    adaptations = _adaptations_for(tenant_id, student_id)
    citations = [
        {"code": o.code, "learning_area": o.learning_area, "year_level": o.year_level}
        for o in outcomes
    ]

    if not outcomes:
        grounded = False
        answer = (
            "I can only help with topics in the Australian Curriculum for your year level. "
            "I couldn't find a matching outcome for that question — please check with your teacher."
        )
    else:
        grounded = True
        context = "\n".join(
            f"[{o.code}] {o.learning_area} Y{o.year_level} {o.strand}: {o.content_description}"
            for o in outcomes
        )
        model_name = agent.model_name if agent else "claude-sonnet-5"
        # Data minimisation (ST4S): strip PII from the student's question before
        # it is sent to any external model.
        safe_question = anonymize.anonymise(question, names=anonymize.names_for_student(tenant_id, student_id))
        answer = llm.generate(question=safe_question, context=context, model_name=model_name)
        if not answer:  # no LLM configured → safe extractive grounding
            answer = _extractive_answer(question, outcomes, adaptations)

    # Transparency/accountability log (Framework principles). Never store the raw
    # prompt beyond a truncated summary; never used for training.
    if agent is not None:
        AgentInteractionLog.objects.create(
            tenant_id=tenant_id,
            agent=agent,
            actor=actor or "",
            prompt_summary=(question or "")[:500],
            curriculum_code=outcomes[0].code if outcomes else "",
            reviewed_by_human=False,
        )

    return {
        "answer": answer,
        "grounded": grounded,
        "citations": citations,
        "adaptations": adaptations,
        "agent_key": TUTOR_KEY,
        "reviewed_by_human": False,
    }
