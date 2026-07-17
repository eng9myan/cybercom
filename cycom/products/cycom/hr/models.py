from django.db import models

from platform.common.models import BaseModel


class Employee(BaseModel):
    EMPLOYMENT_STATUS = [
        ("active", "Active"),
        ("on_leave", "On Leave"),
        ("terminated", "Terminated"),
    ]

    employee_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=150, blank=True)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default="active")

    class Meta:
        db_table = "cycom_hr_employees"
        unique_together = [("tenant_id", "employee_number")]
        ordering = ["employee_number"]

    def __str__(self):
        return f"{self.employee_number} — {self.first_name} {self.last_name}"


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
