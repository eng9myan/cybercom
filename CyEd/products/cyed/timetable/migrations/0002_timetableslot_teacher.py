import django.db.models.deletion
from django.db import migrations, models


def backfill_teacher(apps, schema_editor):
    """
    Link each slot to hr.Staff. Two cases:
      1. The slot's own teacher_name is blank -> it simply teaches whoever
         teaches the class_section, so leave slot.teacher NULL; readers should
         fall back to class_section.teacher (see TimetableSlot.teacher_display).
      2. The slot carries its own teacher_name (a cover/split-class override)
         -> try to match it directly, same rules as the ClassSection backfill.
    Ambiguous/unmatched rows are printed for manual follow-up, same as
    sis 0004_classsection_teacher.
    """
    TimetableSlot = apps.get_model("cyed_timetable", "TimetableSlot")
    Staff = apps.get_model("cyed_hr", "Staff")

    matched = 0
    unmatched = []
    ambiguous = []

    for slot in TimetableSlot.objects.exclude(teacher_name="").iterator():
        name = slot.teacher_name.strip()
        if not name:
            continue
        candidates = list(Staff.objects.filter(tenant_id=slot.tenant_id))
        exact = [
            s for s in candidates
            if f"{s.first_name} {s.last_name}".strip().lower() == name.lower()
        ]
        if len(exact) == 1:
            slot.teacher_id = exact[0].id
            slot.save(update_fields=["teacher"])
            matched += 1
        elif len(exact) > 1:
            ambiguous.append((str(slot.id), name, slot.tenant_id))
        else:
            unmatched.append((str(slot.id), name, slot.tenant_id))

    print(f"\n[0002_timetableslot_teacher] matched {matched} slot(s) with a per-slot teacher_name override.")
    if ambiguous:
        print(f"[0002_timetableslot_teacher] {len(ambiguous)} AMBIGUOUS override(s) — left NULL, resolve manually:")
        for slot_id, name, tenant_id in ambiguous:
            print(f"    slot={slot_id} tenant={tenant_id} teacher_name={name!r}")
    if unmatched:
        print(f"[0002_timetableslot_teacher] {len(unmatched)} UNMATCHED override(s) — left NULL:")
        for slot_id, name, tenant_id in unmatched:
            print(f"    slot={slot_id} tenant={tenant_id} teacher_name={name!r}")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cyed_timetable", "0001_initial"),
        ("cyed_hr", "0003_onboardingtask_performancereview"),
        ("cyed_sis", "0004_classsection_teacher"),
    ]

    operations = [
        migrations.AddField(
            model_name="timetableslot",
            name="teacher",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="timetable_slots", to="cyed_hr.staff",
            ),
        ),
        migrations.RunPython(backfill_teacher, noop_reverse),
    ]
