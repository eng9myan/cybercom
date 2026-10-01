from django.db import models

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel


class Department(BaseModel):
    """Organisational unit: a tree (parent/children) with an optional
    manager. Employees belong to one via Employee.department_unit; the
    legacy free-text Employee.department is kept in sync with its name so
    existing reports/payroll that read the string keep working."""

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="children")
    manager = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="managed_departments")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_hr_departments"
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["tenant_id", "parent", "name"],
                                               name="uniq_department_name_per_parent")]

    def __str__(self):
        return self.name

    def ancestors(self):
        node, seen = self.parent, []
        while node is not None and node.pk not in seen:
            seen.append(node.pk)
            node = node.parent
        return seen

    def descendant_ids(self) -> set:
        out, frontier = set(), [self.pk]
        while frontier:
            kids = list(Department.objects.filter(parent_id__in=frontier).values_list("pk", flat=True))
            frontier = [k for k in kids if k not in out]
            out.update(frontier)
        return out


class Employee(BaseModel):
    EMPLOYMENT_STATUS = [
        ("active", "Active"),
        ("on_leave", "On Leave"),
        ("terminated", "Terminated"),
    ]

    MARITAL_CHOICES = [
        ("single", "Single"),
        ("married", "Married"),
        ("cohabitant", "Legal Cohabitant"),
        ("divorced", "Divorced"),
        ("widower", "Widower"),
    ]

    employee_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Contact PII — encrypted per-tenant. email is blind-indexed for exact-match
    # lookup (Employee.objects.filter(email_bidx=blind_index(value))).
    email = EncryptedText(classification="pii", blind_index=True)
    phone = EncryptedText(classification="pii")
    job_title = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=150, blank=True)
    department_unit = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name="members")
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default="active")
    # Drives the Jordan income-tax personal exemption (18,000 for a married
    # employee whose spouse is not employed, otherwise 9,000).
    marital = models.CharField(max_length=20, choices=MARITAL_CHOICES, default="single")
    spouse_employed = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_hr_employees"
        unique_together = [("tenant_id", "employee_number")]
        ordering = ["employee_number"]

    def __str__(self):
        return f"{self.employee_number} — {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Keep the legacy text field and the real FK in step: a unit wins and
        # sets the text; text alone links to the unit with exactly that name.
        if self.department_unit_id:
            self.department = self.department_unit.name
        elif self.department:
            matches = list(Department.objects.filter(tenant_id=self.tenant_id, name=self.department)[:2])
            if len(matches) == 1:
                self.department_unit = matches[0]
        super().save(*args, **kwargs)


class Contract(BaseModel):
    CONTRACT_TYPES = [
        ("full_time", "Full-Time"),
        ("part_time", "Part-Time"),
        ("temporary", "Temporary"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="contracts")
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, default="full_time")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=10, default="JOD")

    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Standard monthly working hours, used to derive an hourly rate for the
    # overtime/lateness rule engine (26 working days * 8h is the common
    # Jordan-market default; overridable per contract).
    standard_monthly_hours = models.DecimalField(max_digits=6, decimal_places=2, default=208)
    overtime_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.5)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_hr_contracts"
        ordering = ["-start_date"]

    @property
    def hourly_rate(self):
        if not self.standard_monthly_hours:
            return 0
        return self.base_salary / self.standard_monthly_hours

    def __str__(self):
        return f"{self.employee} — {self.contract_type}"


class EmployeeDocument(BaseModel):
    """A compliance document on file for an employee (Iqama/work permit,
    passport, driving license, ...) with an expiry an HR officer needs to
    track. Deliberately its own model rather than reusing the generic
    products.cycom.documents.Document store: that one has no
    document_type/expiry_date fields, and expiry tracking is this
    feature's entire purpose."""

    DOCUMENT_TYPES = [
        ("passport", "Passport"),
        ("iqama", "Iqama / Work Permit"),
        ("visa", "Visa"),
        ("license", "Driving License"),
        ("health_certificate", "Health Certificate"),
        ("other", "Other"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cycom_hr_employee_documents"
        ordering = ["expiry_date"]

    def __str__(self):
        return f"{self.employee} — {self.get_document_type_display()}"


class EmployeeInsurance(BaseModel):
    """A health-insurance enrollment for an employee. Scoped to what
    app/hr/insurance/page.tsx's table actually reads (employee, plan
    name/tier, provider, policy number, coverage dates, status) — the
    page's dependent-count/premium/company-share/employee-deduction
    columns are hardcoded placeholders in its own mapper function, not
    read from any backend field, so there's nothing there yet to wire a
    real field to; that's a frontend gap as much as a backend one, and
    adding that depth is a natural follow-up once the page itself reads it."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="insurance_enrollments")
    plan_name = models.CharField(max_length=150, blank=True)
    provider = models.CharField(max_length=150, blank=True)
    policy_number = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        db_table = "cycom_hr_employee_insurance"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee} — {self.plan_name or self.provider}"
