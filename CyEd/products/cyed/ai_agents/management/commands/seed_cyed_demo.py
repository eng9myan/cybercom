"""
seed_cyed_demo — Education Ready-ERP provisioning bootstrap (Phase 0).

Provisions a demo school for a tenant: an academic year, subjects/class
sections, a student + guardian + enrolment, and the four privacy-first
GenAI agent definitions (tutor + teacher tools). Idempotent per tenant.

    python manage.py seed_cyed_demo [--tenant <uuid>]
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from products.cyed.ai_agents.models import AgentDefinition
from products.cyed.curriculum.models import CurriculumOutcome
from products.cyed.sis.models import AcademicYear, ClassSection, Enrolment, Guardian, Student
from products.cyed.timetable.models import TimetableSlot

DEFAULT_TENANT = "11111111-1111-1111-1111-111111111111"

ACARA_OUTCOMES = [
    {"code": "AC9M8N01", "learning_area": "Mathematics", "year_level": 8, "strand": "Number",
     "content_description": "Recognise irrational numbers and terminating/recurring decimals."},
    {"code": "AC9M8A01", "learning_area": "Mathematics", "year_level": 8, "strand": "Algebra",
     "content_description": "Create and use algebraic expressions and formulas."},
    {"code": "AC9E8LA01", "learning_area": "English", "year_level": 8, "strand": "Language",
     "content_description": "Understand how coherence is created in complex texts."},
    {"code": "AC9S8U01", "learning_area": "Science", "year_level": 8, "strand": "Science Understanding",
     "content_description": "Analyse the properties of matter using the particle model."},
]

AGENTS = [
    {
        "key": "cyed.tutor",
        "name": "Curriculum-Aligned Learning Assistant",
        "capability": "tutor",
        "description": "RAG tutor grounded strictly in the Australian Curriculum (ACARA). "
        "Answers cite the content-description code; student inputs are never used for training.",
        "grounding": "ACARA",
        "no_train": True,
        "human_in_the_loop": False,
    },
    {
        "key": "cyed.lesson_planner",
        "name": "Lesson Plan Generator",
        "capability": "lesson_planner",
        "description": "Generates ACARA-mapped lesson plans; every output routed to the HITL "
        "queue for teacher approval before use.",
        "grounding": "ACARA",
        "human_in_the_loop": True,
    },
    {
        "key": "cyed.rubric",
        "name": "Rubric Generator",
        "capability": "rubric",
        "description": "Builds assessment rubrics aligned to achievement standards. Human-in-the-loop.",
        "grounding": "ACARA",
        "human_in_the_loop": True,
    },
    {
        "key": "cyed.differentiator",
        "name": "Differentiated Task Generator",
        "capability": "differentiator",
        "description": "Produces tiered tasks (incl. EAL/D scaffolding) from a learner profile. HITL.",
        "grounding": "ACARA",
        "human_in_the_loop": True,
    },
    {
        "key": "cyed.integrity",
        "name": "Academic Integrity / Authenticity",
        "capability": "integrity",
        "description": "Process-provenance authenticity signals (draft lineage, disclosure). "
        "Flags route to a human decision — never auto-accuses.",
        "grounding": "TEQSA",
        "human_in_the_loop": True,
    },
]


class Command(BaseCommand):
    help = "Seed a demo CyEd school + GenAI agent definitions for a tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=DEFAULT_TENANT, help="Tenant UUID to seed.")

    @transaction.atomic
    def handle(self, *args, **options):
        tenant = options["tenant"]

        year, _ = AcademicYear.objects.get_or_create(
            tenant_id=tenant, name="2026",
            defaults={"start_date": date(2026, 1, 28), "end_date": date(2026, 12, 18), "is_current": True},
        )

        section, _ = ClassSection.objects.get_or_create(
            tenant_id=tenant, name="8A Mathematics",
            defaults={"subject": "Mathematics", "year_level": 8, "teacher_name": "Mr. Ellis",
                      "room": "B12", "academic_year": year},
        )

        guardian, _ = Guardian.objects.get_or_create(
            tenant_id=tenant, first_name="Sarah", last_name="Nguyen",
            defaults={"relationship": "mother", "email": "sarah.nguyen@example.com",
                      "is_primary_contact": True},
        )

        student, created = Student.objects.get_or_create(
            tenant_id=tenant, first_name="Minh", last_name="Nguyen",
            defaults={"student_number": "S0001", "year_level": 8, "enrolment_status": "enrolled"},
        )
        if created:
            student.guardians.add(guardian)

        Enrolment.objects.get_or_create(
            tenant_id=tenant, student=student, class_section=section,
            defaults={"status": "active", "enrolled_on": date(2026, 1, 28)},
        )

        TimetableSlot.objects.get_or_create(
            tenant_id=tenant, class_section=section, day_of_week="mon", period_label="Period 1",
            defaults={"start_time": "09:00", "end_time": "10:00", "room": "B12", "teacher_name": "Mr. Ellis"},
        )

        outcomes_created = 0
        for spec in ACARA_OUTCOMES:
            _, made = CurriculumOutcome.objects.get_or_create(
                tenant_id=tenant, code=spec["code"], framework="ACARA v9",
                defaults={
                    "learning_area": spec["learning_area"],
                    "year_level": spec["year_level"],
                    "strand": spec.get("strand", ""),
                    "content_description": spec.get("content_description", ""),
                },
            )
            outcomes_created += int(made)

        agents_created = 0
        for spec in AGENTS:
            _, made = AgentDefinition.objects.get_or_create(
                tenant_id=tenant, key=spec["key"],
                defaults={
                    "name": spec["name"],
                    "capability": spec["capability"],
                    "description": spec["description"],
                    "grounding": spec.get("grounding", "ACARA"),
                    "no_train": spec.get("no_train", True),
                    "human_in_the_loop": spec.get("human_in_the_loop", True),
                },
            )
            agents_created += int(made)

        # Load the broader bundled ACARA v9 starter set so AI grounding works
        # across F-10, not just the handful above (idempotent upsert).
        from django.core.management import call_command
        call_command("import_curriculum", tenant=str(tenant))

        self.stdout.write(self.style.SUCCESS(
            f"CyEd demo seeded for tenant {tenant}: "
            f"1 academic year, 1 class section, 1 timetable slot, 1 student, "
            f"{len(ACARA_OUTCOMES)} ACARA outcomes ({outcomes_created} new) + starter set, "
            f"{len(AGENTS)} agents ({agents_created} new)."
        ))
