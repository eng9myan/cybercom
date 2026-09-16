"""
seed_academic_year — generate a realistic full year of school data.

Every audit since 2026-08-09 named this as the highest-value next step, because
it is the only way to answer the questions nobody could: does the system hold
up at a real school's volume, and do the reports still agree with each other
after a year of transactions?

    python manage.py seed_academic_year --campuses 3 --students-per-campus 200
    python manage.py seed_academic_year --scale small        # a quick smoke run
    python manage.py seed_academic_year --profile            # time the reports

Deliberately deterministic: a fixed RNG seed means two runs produce identical
data, so a slow report can be re-measured after a fix against the same rows
rather than against a fresh random population.

Idempotent per tenant *by academic year* — re-running for a year that already
has data refuses rather than silently doubling every student's fees.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.billing.models import BillLineItem, FeePlan, SiblingDiscountRule, StudentBill
from products.cyed.billing.services import generate_installments, record_payment
from products.cyed.finance.models import Account
from products.cyed.finance.services import post_entry
from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.hr.models import Contract, Staff
from products.cyed.hr.testing import clear_for_teaching
from products.cyed.org.models import Campus
from products.cyed.sis.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    Family,
    Guardian,
    Student,
)
from products.cyed.timetable.models import TimetableSlot

DEFAULT_TENANT = "11111111-1111-1111-1111-111111111111"

SCALES = {
    "small": {"campuses": 1, "students_per_campus": 30, "weeks": 4},
    "medium": {"campuses": 3, "students_per_campus": 200, "weeks": 20},
    "large": {"campuses": 13, "students_per_campus": 600, "weeks": 40},
}

# Named sites, so a group demo reads as four schools rather than "Campus 1..4".
# Beyond this list the seeder falls back to numbered campuses — a 13-campus
# load test does not need invented names.
CAMPUS_ROSTER = [
    ("Parramatta Senior College", "PARR", "Parramatta", "NSW", "2150", "Dr Helen Fraser"),
    ("Blacktown Junior School", "BLKT", "Blacktown", "NSW", "2148", "Michael Osei"),
    ("Liverpool Campus", "LIVE", "Liverpool", "NSW", "2170", "Rebecca Tran"),
    ("Penrith Campus", "PENR", "Penrith", "NSW", "2750", "Sanjay Mehta"),
    ("Newcastle Campus", "NEWC", "Newcastle", "NSW", "2300", "Alice Duncan"),
    ("Wollongong Campus", "WOLL", "Wollongong", "NSW", "2500", "Peter Nguyen"),
]

SUBJECTS = ["Mathematics", "English", "Science", "HASS", "Health and PE", "The Arts"]
DAYS = ["mon", "tue", "wed", "thu", "fri"]
PERIODS = [("P1", "09:00", "10:00"), ("P2", "10:00", "11:00"), ("P3", "11:30", "12:30")]

FIRST_NAMES = [
    "Ana", "Ben", "Cara", "Dev", "Eve", "Finn", "Grace", "Hugo", "Ivy", "Jack",
    "Kira", "Liam", "Mia", "Noah", "Olive", "Pia", "Quinn", "Ravi", "Sana", "Tom",
]
SURNAMES = [
    "Nguyen", "Smith", "Patel", "Tran", "Wong", "Brown", "Singh", "Lee", "Jones",
    "Ali", "Martin", "Chen", "Kaur", "Wilson", "Ito", "Costa", "Novak", "Dube",
]

# Roughly reflects a real school: most students present most days.
ATTENDANCE_WEIGHTS = [("present", 92), ("absent", 4), ("late", 3), ("excused", 1)]

# Real schools have a tail. Giving every student identical odds produces a
# population where nobody falls below 90% — so the chronic-absence list, the
# cohort a school is actually held to account for, comes back empty and the
# leadership screen looks broken rather than clean. About one student in
# fourteen attends materially worse than their peers.
CHRONIC_SHARE = 0.07
CHRONIC_WEIGHTS = [("present", 68), ("absent", 24), ("late", 5), ("excused", 3)]

# A–E weighted toward the middle. Picking uniformly gives every grade a flat
# 20% share, which no real cohort produces and which makes an achievement
# distribution read as obviously synthetic to anyone who has seen one.
ACHIEVEMENT_LEVELS = ["A", "B", "C", "D", "E"]
ACHIEVEMENT_WEIGHTS = [12, 26, 34, 20, 8]
# Score bands matching each letter, so a mark and its letter agree — a "B"
# sitting next to 41/100 is the kind of detail that ends a demo.
SCORE_BANDS = {"A": (85, 100), "B": (70, 84), "C": (55, 69), "D": (40, 54), "E": (15, 39)}


class Command(BaseCommand):
    help = "Seed a full academic year of realistic data for load testing."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=DEFAULT_TENANT)
        parser.add_argument("--year", type=int, default=2026)
        parser.add_argument("--scale", choices=sorted(SCALES), default="medium")
        parser.add_argument("--campuses", type=int)
        parser.add_argument("--students-per-campus", type=int)
        parser.add_argument("--weeks", type=int, help="Weeks of attendance and assessment.")
        parser.add_argument("--seed", type=int, default=20260812)
        parser.add_argument(
            "--profile", action="store_true",
            help="Time the reports the audits flagged as aggregating in Python.",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Seed even if this academic year already has data (will duplicate).",
        )

    def handle(self, *args, **options):
        scale = SCALES[options["scale"]]
        tenant = options["tenant"]
        year = options["year"]
        campuses = options["campuses"] or scale["campuses"]
        per_campus = options["students_per_campus"] or scale["students_per_campus"]
        weeks = options["weeks"] or scale["weeks"]

        random.seed(options["seed"])

        existing = AcademicYear.objects.filter(tenant_id=tenant, name=str(year)).first()
        if existing and not options["force"]:
            raise CommandError(
                f"Academic year {year} already exists for this tenant. Re-running would "
                f"double every student's fees. Pass --force if that is what you want."
            )

        started = timezone.now()
        self.stdout.write(
            f"Seeding {campuses} campus(es) × {per_campus} students × {weeks} weeks…"
        )

        with transaction.atomic():
            counts = self._seed(tenant, year, campuses, per_campus, weeks)

        elapsed = (timezone.now() - started).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"\nSeeded in {elapsed:.1f}s:"))
        for label, value in counts.items():
            self.stdout.write(f"  {label:.<32} {value:,}")

        if options["profile"]:
            self._profile(tenant)

    # ── seeding ─────────────────────────────────────────────────────────────
    def _seed(self, tenant, year, campus_count, per_campus, weeks):
        counts = {}
        academic_year = AcademicYear.objects.create(
            tenant_id=tenant, name=str(year),
            start_date=date(year, 1, 28), end_date=date(year, 12, 11),
        )
        self._chart_of_accounts(tenant)

        plan = FeePlan.objects.create(
            tenant_id=tenant, name=f"{year} Termly", schedule_type="termly",
            installments_count=3, late_fee_percent=Decimal("2"),
        )
        SiblingDiscountRule.objects.get_or_create(
            tenant_id=tenant, ordinal=2, academic_year=None, campus=None,
            defaults={"name": "Second child", "percent": Decimal("10")},
        )
        SiblingDiscountRule.objects.get_or_create(
            tenant_id=tenant, ordinal=3, academic_year=None, campus=None,
            defaults={"name": "Third child and beyond", "percent": Decimal("25")},
        )

        campuses, staff, sections, students, families = [], [], [], [], []

        for c in range(campus_count):
            if c < len(CAMPUS_ROSTER):
                name, code, suburb, state, postcode, principal = CAMPUS_ROSTER[c]
            else:
                name, code = f"Campus {c + 1}", f"C{c + 1:02d}"
                suburb = state = postcode = principal = ""
            campus = Campus.objects.create(
                tenant_id=tenant, name=name, code=code, suburb=suburb, state=state,
                postcode=postcode, principal_name=principal,
                address=f"{10 + c} School Road" if suburb else "",
            )
            campuses.append(campus)
            campus_staff = self._staff_for(tenant, campus, c)
            staff.extend(campus_staff)
            campus_sections = self._sections_for(tenant, campus, academic_year, campus_staff)
            sections.extend(campus_sections)
            campus_students, campus_families = self._students_for(
                tenant, campus, per_campus, campus_sections
            )
            students.extend(campus_students)
            families.extend(campus_families)

        counts["campuses"] = len(campuses)
        counts["staff"] = len(staff)
        counts["class sections"] = len(sections)
        counts["families"] = len(families)
        counts["students"] = len(students)

        counts["timetable slots"] = self._timetable(tenant, sections)
        counts["bills"] = self._billing(tenant, students, academic_year, plan)
        counts["attendance marks"] = self._attendance(tenant, sections, year, weeks)
        counts["grades"] = self._assessment(tenant, sections, year, weeks)
        counts["journal entries"] = self._ledger(tenant, year, weeks)
        return counts

    def _chart_of_accounts(self, tenant):
        for code, name, kind in [
            ("1100", "Accounts Receivable", "asset"),
            ("1200", "Bank", "asset"),
            ("4000", "Tuition Income", "income"),
            ("5000", "Salaries", "expense"),
            ("5100", "Operating Expenses", "expense"),
        ]:
            Account.objects.get_or_create(
                tenant_id=tenant, code=code, defaults={"name": name, "account_type": kind}
            )

    def _staff_for(self, tenant, campus, index):
        """Enough teachers to cover the sections, all cleared to teach."""
        people = []
        for i in range(len(SUBJECTS) * 2):
            person = Staff.objects.create(
                tenant_id=tenant, campus=campus,
                first_name=FIRST_NAMES[(index * 7 + i) % len(FIRST_NAMES)],
                last_name=SURNAMES[(index * 5 + i) % len(SURNAMES)],
                role="teacher", staff_number=f"T{index:02d}{i:03d}",
                email=f"teacher{index}.{i}@cyed.edu.au",
            )
            Contract.objects.create(
                tenant_id=tenant, staff=person, contract_type="full_time",
                annual_salary=Decimal("96000"), fte=Decimal("1"), is_current=True,
            )
            clear_for_teaching(person)
            people.append(person)
        return people

    def _sections_for(self, tenant, campus, academic_year, staff):
        sections = []
        for year_level in (7, 8, 9, 10):
            for i, subject in enumerate(SUBJECTS):
                sections.append(ClassSection.objects.create(
                    tenant_id=tenant, campus=campus, academic_year=academic_year,
                    name=f"{year_level}{chr(65 + i)} {subject}",
                    subject=subject, year_level=year_level,
                    teacher=staff[i % len(staff)], capacity=30,
                ))
        return sections

    def _students_for(self, tenant, campus, count, sections):
        """
        Students grouped into households, so sibling pricing is exercised
        rather than every child being an only child.
        """
        students, families = [], []
        i = 0
        while len(students) < count:
            family = Family.objects.create(
                tenant_id=tenant, name=f"{SURNAMES[i % len(SURNAMES)]} Household {i}"
            )
            families.append(family)
            guardian = Guardian.objects.create(
                tenant_id=tenant, family=family,
                first_name=FIRST_NAMES[i % len(FIRST_NAMES)],
                last_name=SURNAMES[i % len(SURNAMES)],
                email=f"guardian{campus.code}{i}@example.com", phone="0400000000",
            )
            family.billing_contact = guardian
            family.save(update_fields=["billing_contact"])

            # 1–3 children per household, weighted toward smaller families.
            for _ in range(random.choices([1, 2, 3], weights=[55, 33, 12])[0]):
                if len(students) >= count:
                    break
                year_level = random.choice([7, 8, 9, 10])
                student = Student.objects.create(
                    tenant_id=tenant, campus=campus, family=family,
                    first_name=FIRST_NAMES[len(students) % len(FIRST_NAMES)],
                    last_name=family.name.split()[0],
                    year_level=year_level, enrolment_status="enrolled",
                    student_number=f"{campus.code}{len(students):05d}",
                    date_of_birth=date(2026 - year_level - 5, 1 + (len(students) % 12), 15),
                    # A student without an email cannot be signed in as, and the
                    # student portal scopes on it — so seeded data that omits it
                    # makes a whole role untestable.
                    email=f"{campus.code}{len(students):05d}@students.cyed.edu.au".lower(),
                )
                student.guardians.add(guardian)
                for section in [s for s in sections if s.year_level == year_level]:
                    Enrolment.objects.create(
                        tenant_id=tenant, student=student, class_section=section, status="active"
                    )
                students.append(student)
            i += 1
        return students, families

    def _timetable(self, tenant, sections):
        slots = []
        for i, section in enumerate(sections):
            day = DAYS[i % len(DAYS)]
            label, start, end = PERIODS[i % len(PERIODS)]
            slots.append(TimetableSlot(
                tenant_id=tenant, class_section=section, day_of_week=day,
                period_label=label, start_time=start, end_time=end,
                teacher=section.teacher, room=f"R{i % 20 + 1}",
            ))
        TimetableSlot.objects.bulk_create(slots)
        return len(slots)

    def _billing(self, tenant, students, academic_year, plan):
        for student in students:
            bill = StudentBill.objects.create(
                tenant_id=tenant, student=student, plan=plan,
                academic_year=academic_year, campus=student.campus, status="draft",
                start_date=academic_year.start_date,
            )
            BillLineItem.objects.create(
                tenant_id=tenant, bill=bill, category="tuition",
                description="Annual tuition", amount=Decimal("6000.00"),
            )
            generate_installments(bill, start_date=academic_year.start_date)

            # Most families pay most installments; some fall behind, which is
            # what makes the aging report and the dunning ladder meaningful.
            for installment in bill.installments.order_by("installment_no"):
                if random.random() < 0.75:
                    record_payment(installment, amount=installment.amount_due, method="bpay")
        return len(students)

    def _attendance(self, tenant, sections, year, weeks):
        """One roll per section per week — the dominant row count in a real school."""
        statuses = [s for s, _ in ATTENDANCE_WEIGHTS]
        weights = [w for _, w in ATTENDANCE_WEIGHTS]
        chronic_weights = [w for _, w in CHRONIC_WEIGHTS]
        term_start = date(year, 1, 28)
        total = 0

        # Chosen once per student, not per mark: a poor attender is a person
        # with a pattern, not a run of unlucky dice, and the same child has to
        # look poor across every class they take or the per-student rate
        # averages back out to the cohort mean.
        all_students = list(
            Student.objects.filter(tenant_id=tenant).values_list("id", flat=True)
        )
        chronic = set(
            random.sample(all_students, int(len(all_students) * CHRONIC_SHARE))
        )

        for section in sections:
            roster = list(
                Enrolment.objects.filter(
                    tenant_id=tenant, class_section=section, status="active"
                ).values_list("student_id", flat=True)
            )
            if not roster:
                continue
            for week in range(weeks):
                day = term_start + timedelta(weeks=week)
                roll = RollCall.objects.create(
                    tenant_id=tenant, class_section=section, date=day, period_label="P1",
                    taken_by="seed@cyed.edu.au",
                )
                marks = [
                    AttendanceMark(
                        tenant_id=tenant, roll_call=roll, student_id=sid,
                        status=random.choices(
                            statuses,
                            weights=chronic_weights if sid in chronic else weights,
                        )[0],
                    )
                    for sid in roster
                ]
                # bulk_create fires no signals, so the seed does not generate a
                # guardian notification for every simulated absence — tens of
                # thousands of messages nobody asked for.
                AttendanceMark.objects.bulk_create(marks)
                total += len(marks)
        return total

    def _assessment(self, tenant, sections, year, weeks):
        total = 0
        for section in sections:
            roster = list(
                Enrolment.objects.filter(
                    tenant_id=tenant, class_section=section, status="active"
                ).values_list("student_id", flat=True)
            )
            if not roster:
                continue
            for n in range(max(1, weeks // 5)):
                assessment = Assessment.objects.create(
                    tenant_id=tenant, class_section=section,
                    name=f"{section.subject} Task {n + 1}",
                    assessment_type="summative", max_score=Decimal("100"),
                    due_date=date(year, 3, 1) + timedelta(weeks=n * 5),
                )
                graded = []
                for sid in roster:
                    letter = random.choices(
                        ACHIEVEMENT_LEVELS, weights=ACHIEVEMENT_WEIGHTS
                    )[0]
                    low, high = SCORE_BANDS[letter]
                    graded.append(Grade(
                        tenant_id=tenant, assessment=assessment, student_id=sid,
                        score=Decimal(random.randint(low, high)),
                        achievement_level=letter,
                    ))
                Grade.objects.bulk_create(graded)
                total += len(roster)
        return total

    def _ledger(self, tenant, year, weeks):
        """Enough posted entries that the trial balance has real work to do."""
        receivable = Account.objects.get(tenant_id=tenant, code="1100")
        bank = Account.objects.get(tenant_id=tenant, code="1200")
        income = Account.objects.get(tenant_id=tenant, code="4000")
        salaries = Account.objects.get(tenant_id=tenant, code="5000")

        entries = 0
        for week in range(weeks):
            day = date(year, 1, 28) + timedelta(weeks=week)
            post_entry(
                tenant_id=tenant, date=day, reference=f"FEES-{week:03d}",
                narration="Weekly fee income",
                lines=[
                    {"account_id": receivable.id, "debit": Decimal("25000"), "credit": 0},
                    {"account_id": income.id, "debit": 0, "credit": Decimal("25000")},
                ],
            )
            post_entry(
                tenant_id=tenant, date=day, reference=f"PAY-{week:03d}",
                narration="Payroll",
                lines=[
                    {"account_id": salaries.id, "debit": Decimal("18000"), "credit": 0},
                    {"account_id": bank.id, "debit": 0, "credit": Decimal("18000")},
                ],
            )
            entries += 2
        return entries

    # ── profiling ───────────────────────────────────────────────────────────
    def _profile(self, tenant):
        """
        Time the reports the audits flagged, and count the queries each issues.

        Query count matters more than wall clock on a seeded SQLite database:
        a report whose query count grows with the data will be fine here and
        fall over in production.
        """
        from django.db import connection, reset_queries
        from django.test.utils import CaptureQueriesContext

        from products.cyed.finance.services import (
            ar_aging,
            balance_sheet,
            profit_and_loss,
            trial_balance,
        )

        checks = [
            ("trial_balance", lambda: trial_balance(tenant)),
            ("profit_and_loss", lambda: profit_and_loss(tenant)),
            ("balance_sheet", lambda: balance_sheet(tenant)),
            ("ar_aging", lambda: ar_aging(tenant)),
        ]

        self.stdout.write(self.style.SUCCESS("\nReport profile:"))
        self.stdout.write(f"  {'report':<20} {'seconds':>9} {'queries':>9}")
        for name, fn in checks:
            reset_queries()
            started = timezone.now()
            with CaptureQueriesContext(connection) as captured:
                fn()
            elapsed = (timezone.now() - started).total_seconds()
            flag = "" if len(captured) < 50 else "  ← grows with data"
            self.stdout.write(f"  {name:<20} {elapsed:>9.3f} {len(captured):>9}{flag}")
