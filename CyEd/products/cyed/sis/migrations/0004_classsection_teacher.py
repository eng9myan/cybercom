import django.db.models.deletion
from django.db import migrations, models


def backfill_teacher_by_name(apps, schema_editor):
    """
    Best-effort link of ClassSection.teacher_name (free text) to hr.Staff,
    scoped per tenant, matched on "first_name last_name" case-insensitively.

    Ambiguous matches (two staff sharing the same name in the same tenant)
    and rows with no match at all are left untouched (teacher stays NULL) and
    are printed here so they show up in the `manage.py migrate` output for a
    human to resolve — this is a data-quality problem, not something safe to
    guess at silently.
    """
    ClassSection = apps.get_model("cyed_sis", "ClassSection")
    Staff = apps.get_model("cyed_hr", "Staff")

    matched = 0
    unmatched = []
    ambiguous = []

    sections = ClassSection.objects.exclude(teacher_name="").select_related(None)
    for section in sections.iterator():
        name = section.teacher_name.strip()
        if not name:
            continue
        candidates = list(
            Staff.objects.filter(tenant_id=section.tenant_id)
            .annotate()
        )
        # annotate() with a concat isn't available pre-model-swap safely across
        # DB backends here, so match in Python against the (small) per-tenant
        # staff list instead of a DB expression.
        exact = [
            s for s in candidates
            if f"{s.first_name} {s.last_name}".strip().lower() == name.lower()
        ]
        if len(exact) == 1:
            section.teacher_id = exact[0].id
            section.save(update_fields=["teacher"])
            matched += 1
        elif len(exact) > 1:
            ambiguous.append((str(section.id), name, section.tenant_id))
        else:
            unmatched.append((str(section.id), name, section.tenant_id))

    print(f"\n[0004_classsection_teacher] matched {matched} class section(s) to hr.Staff by name.")
    if ambiguous:
        print(f"[0004_classsection_teacher] {len(ambiguous)} AMBIGUOUS name match(es) — left NULL, resolve manually:")
        for section_id, name, tenant_id in ambiguous:
            print(f"    class_section={section_id} tenant={tenant_id} teacher_name={name!r}")
    if unmatched:
        print(f"[0004_classsection_teacher] {len(unmatched)} UNMATCHED teacher_name value(s) — left NULL:")
        for section_id, name, tenant_id in unmatched:
            print(f"    class_section={section_id} tenant={tenant_id} teacher_name={name!r}")


def noop_reverse(apps, schema_editor):
    # Reversing would require re-deriving teacher_name from the FK, which is
    # already present and untouched by the forward migration — nothing to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cyed_sis", "0003_family_guardian_family_student_family"),
        ("cyed_hr", "0003_onboardingtask_performancereview"),
    ]

    operations = [
        migrations.AddField(
            model_name="classsection",
            name="teacher",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="class_sections", to="cyed_hr.staff",
            ),
        ),
        migrations.RunPython(backfill_teacher_by_name, noop_reverse),
    ]
