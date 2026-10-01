"""Create a Department for every distinct free-text department already on
employees (per tenant) and link those employees to it, so existing data
shows up in the department tree instead of starting empty."""
from django.db import migrations


def forwards(apps, schema_editor):
    Employee = apps.get_model("cycom_hr", "Employee")
    Department = apps.get_model("cycom_hr", "Department")
    pairs = (Employee.objects.exclude(department="").filter(department_unit__isnull=True)
             .values_list("tenant_id", "department").distinct())
    for tenant_id, name in pairs:
        dept = Department.objects.filter(tenant_id=tenant_id, name=name, parent__isnull=True).first()
        if dept is None:
            dept = Department.objects.create(tenant_id=tenant_id, name=name)
        Employee.objects.filter(tenant_id=tenant_id, department=name, department_unit__isnull=True) \
            .update(department_unit=dept)


class Migration(migrations.Migration):
    dependencies = [("cycom_hr", "0008_departments")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
