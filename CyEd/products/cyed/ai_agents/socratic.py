"""
Student AI — Socratic mode (doc requirement: "Zero Direct Answers").

Unlike the tutor (which explains), the Socratic assistant NEVER outputs the
answer or a worked solution. It returns guiding questions and small hints,
grounded in retrieved ACARA curriculum, and declines anything off-curriculum.
Student input is anonymised before any LLM call (ST4S data minimisation) and
every interaction is logged.
"""

from products.cyed.ai_agents import anonymize, llm
from products.cyed.ai_agents.models import AgentDefinition, AgentInteractionLog
from products.cyed.ai_agents.retrieval import retrieve_outcomes

TUTOR_KEY = "cyed.tutor"

# Deterministic guiding questions (used when no LLM is configured). These never
# reveal the answer — they scaffold the student's own thinking.
_GUIDES = [
    "What do you already know about {strand}? Start with what feels certain.",
    "Which part of this question is the tricky bit for you?",
    "Is there a definition, rule, or example from {code} that might apply here?",
    "What would happen if you tried a smaller or simpler version first?",
    "How could you check whether your next step is reasonable?",
]


def ask(*, tenant_id, question, student_id=None, year_level=None, learning_area=None, actor=""):
    agent = AgentDefinition.objects.filter(tenant_id=tenant_id, key=TUTOR_KEY, is_active=True).first()

    # Anonymise the student's question before it touches any model.
    names = anonymize.names_for_student(tenant_id, student_id)
    safe_question = anonymize.anonymise(question, names=names)

    outcomes = retrieve_outcomes(tenant_id, safe_question, year_level=year_level, learning_area=learning_area)

    if not outcomes:
        result = {
            "socratic": True,
            "grounded": False,
            "answer_withheld": True,
            "guiding_questions": [],
            "response": (
                "I can only help with topics in your curriculum. Let's look at "
                "something from your subject — which topic are you studying?"
            ),
            "citations": [],
            "agent_key": TUTOR_KEY,
        }
    else:
        o = outcomes[0]
        strand = o.strand or o.learning_area or "this topic"
        context = "\n".join(
            f"[{x.code}] {x.learning_area} Y{x.year_level} {x.strand}: {x.content_description}"
            for x in outcomes
        )
        llm_text = llm.generate(
            question=safe_question, context=context,
            model_name=agent.model_name if agent else "claude-sonnet-5",
            system=llm.SOCRATIC_SYSTEM_PROMPT,
        )
        guiding = [g.format(strand=strand, code=o.code) for g in _GUIDES]
        if llm_text:
            response = llm_text
        else:
            response = "Let's work through this together — I won't give the answer, but I'll guide you:\n" + \
                "\n".join(f"• {q}" for q in guiding)
        result = {
            "socratic": True,
            "grounded": True,
            "answer_withheld": True,
            "guiding_questions": guiding,
            "response": response,
            "citations": [
                {"code": x.code, "learning_area": x.learning_area, "year_level": x.year_level}
                for x in outcomes
            ],
            "agent_key": TUTOR_KEY,
        }

    if agent is not None:
        AgentInteractionLog.objects.create(
            tenant_id=tenant_id, agent=agent, actor=actor or "",
            prompt_summary=safe_question[:500],  # already anonymised
            curriculum_code=outcomes[0].code if outcomes else "",
            reviewed_by_human=False,
        )
    return result
