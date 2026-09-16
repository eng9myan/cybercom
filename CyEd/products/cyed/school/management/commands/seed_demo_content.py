"""
Fill the modules a demo actually gets clicked through.

`seed_academic_year` builds the spine — students, classes, attendance, grades,
bills. Everything else ships empty, so an evaluator opening Library, Admissions,
Procurement or Wellbeing sees "no records yet" and reasonably concludes the
module is not built. It is; it just has nothing in it.

This command fills those modules with a small, plausible, **idempotent** set.
Re-running it does not duplicate: every row is matched on a natural key first.
It never invents money movement that the finance reports would then disagree
with — purchase orders stay in `draft`/`ordered` rather than received, because
receiving posts to the general ledger.

    python manage.py seed_demo_content
    python manage.py seed_demo_content --tenant <uuid>
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

DEV_TENANT = "11111111-1111-1111-1111-111111111111"

BOOKS = [
    ("Storm Boy", "Colin Thiele", "Fiction"),
    ("Rabbit-Proof Fence", "Doris Pilkington", "Australian history"),
    ("The Rosie Project", "Graeme Simsion", "Fiction"),
    ("Deadly Unna?", "Phillip Gwynne", "Fiction"),
    ("Australian Birds: A Field Guide", "Ken Simpson", "Reference"),
    ("Cosmos", "Carl Sagan", "Science"),
    ("The Happiest Refugee", "Anh Do", "Biography"),
    ("Mathematics Methods Units 1 & 2", "ATAR Press", "Textbook"),
]

SUPPLIERS = [
    ("Officeworks Business", "12 345 678 901", "business@officeworks.example"),
    ("Modern Teaching Aids", "98 765 432 109", "orders@mta.example"),
    ("Campus Cleaning Services", "45 678 901 234", "accounts@campusclean.example"),
]

INVENTORY = [
    ("A4 Copy Paper (box)", "STA-001", "Stationery", "box", 42, 20, "Store room 1"),
    ("Whiteboard Markers (pack)", "STA-014", "Stationery", "pack", 8, 15, "Store room 1"),
    ("Chromebook 11\"", "ICT-220", "ICT", "unit", 35, 10, "ICT store"),
    ("First Aid Kit Refill", "MED-003", "Medical", "kit", 4, 6, "Sick bay"),
    ("Science Safety Goggles", "SCI-050", "Science", "unit", 60, 25, "Lab prep"),
]

ASSETS = [
    ("Interactive Panel — Room 12", "AV-0012", "AV equipment", "Room 12", "4200.00", 8),
    ("Toyota Coaster Bus", "VEH-0001", "Vehicle", "Bus bay", "78000.00", 12),
    ("Server — Rack A", "ICT-0001", "ICT infrastructure", "Comms room", "9600.00", 5),
]

NOTICES = [
    ("Swimming carnival — Friday", "Buses leave at 8:40am sharp from the front gate. Students travel in house colours and must bring a hat, sunscreen and a labelled water bottle.", "all", "important"),
    ("Winter uniform from Monday", "Full winter uniform applies from Monday. Blazers are required for assembly and for travel to and from school.", "parents", "normal"),
    ("Year 12 study hall — new room", "Year 12 study hall moves to the library seminar room for the rest of term.", "students", "normal"),
    ("Staff briefing moved to 8:15am", "Tomorrow's staff briefing starts fifteen minutes earlier to cover the evacuation drill.", "staff", "urgent"),
]

APPLICANTS = [
    ("Amelia", "Whitfield", 7, "enquiry", "Open day"),
    ("Noah", "Okafor", 8, "submitted", "Website"),
    ("Sophia", "Rinaldi", 7, "assessment", "Referral"),
    ("Kai", "Tupuola", 9, "offer", "Website"),
    ("Harper", "Nguyen", 7, "accepted", "Sibling"),
    ("Lucas", "Bauer", 10, "waitlisted", "Open day"),
    ("Zara", "Haddad", 8, "declined", "Website"),
]

POSITIVE = [
    "Outstanding contribution to class discussion.",
    "Helped a new student settle in without being asked.",
    "Consistent effort on homework all term.",
    "Represented the school well at the debating final.",
]
MINOR = [
    "Late to class without a note.",
    "Repeatedly off-task during independent work.",
    "Uniform breach — no blazer at assembly.",
]
MAJOR = [
    "Disrespectful language towards a staff member.",
    "Left the school grounds at lunch without permission.",
]


class Command(BaseCommand):
    help = "Fill library, admissions, wellbeing, HR, procurement and the rest with demo content."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=DEV_TENANT)
        parser.add_argument("--seed", type=int, default=20260814)

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        tenant = options["tenant"]
        today = timezone.localdate()

        from products.cyed.hr.models import Staff
        from products.cyed.org.models import Campus
        from products.cyed.sis.models import ClassSection, Student

        students = list(Student.objects.filter(tenant_id=tenant, enrolment_status="enrolled"))
        staff = list(Staff.objects.filter(tenant_id=tenant))
        sections = list(ClassSection.objects.filter(tenant_id=tenant))
        campuses = list(Campus.objects.filter(tenant_id=tenant))
        if not students:
            self.stderr.write(
                "No students in this tenant. Run `seed_academic_year` first — this "
                "command fills in around that spine, it does not create it."
            )
            return

        counts = {}
        counts.update(self._library(tenant, students, today))
        counts.update(self._admissions(tenant, today, campuses))
        counts.update(self._notices(tenant, staff, today, campuses))
        counts.update(self._health(tenant, students, today))
        counts.update(self._wellbeing(tenant, students, staff, today))
        counts.update(self._messaging(tenant, students, staff))
        counts.update(self._lms(tenant, sections))
        counts.update(self._assessment(tenant, sections, today))
        counts.update(self._hr(tenant, staff, today))
        counts.update(self._procurement(tenant))
        counts.update(self._inventory_assets(tenant, today))
        counts.update(self._transport(tenant, students))
        counts.update(self._visitors(tenant, staff))
        counts.update(self._reports(tenant, students, sections))
        counts.update(self._relief(tenant, today, campuses))
        counts.update(self._interviews(tenant, staff, today))
        counts.update(self._exams(tenant, students, today, campuses))
        counts.update(self._learner_profiles(tenant, students, today))
        counts.update(self._payroll_and_attendance(tenant, staff, today))
        counts.update(self._docsign(tenant, staff, students, today))
        counts.update(self._nccd(tenant, students, today))

        self.stdout.write(self.style.SUCCESS("\nDemo content ready:"))
        for label, n in counts.items():
            self.stdout.write(f"  {label:.<34} {n}")

    # ── modules ──────────────────────────────────────────────────────────────
    def _library(self, tenant, students, today):
        from products.cyed.library.models import Book, LibraryPolicy, Loan

        LibraryPolicy.objects.get_or_create(
            tenant_id=tenant,
            defaults=dict(max_loans_per_student=4, loan_days=14, fine_per_day=Decimal("0.20"),
                          max_fine_per_loan=Decimal("10.00"), grace_days=2),
        )
        books = []
        for title, author, category in BOOKS:
            book, _ = Book.objects.get_or_create(
                tenant_id=tenant, title=title,
                defaults=dict(author=author, category=category, copies_total=3, copies_available=3),
            )
            books.append(book)

        loans = 0
        # One overdue on purpose: the fine calculation is the interesting part
        # of this module and an all-current shelf never exercises it.
        # Roughly one student in twelve has something out, capped so a
        # 13-campus load run does not spend its time here.
        borrowers = students[: max(6, min(len(students) // 12, 400))]
        for i, student in enumerate(borrowers):
            book = books[i % len(books)]
            borrowed = today - timedelta(days=30 if i == 0 else 5)
            loan, created = Loan.objects.get_or_create(
                tenant_id=tenant, book=book, student=student, returned_on=None,
                defaults=dict(borrowed_on=borrowed, due_on=borrowed + timedelta(days=14),
                              status="borrowed"),
            )
            if created:
                loans += 1
        return {"library books": len(books), "loans": loans}

    def _admissions(self, tenant, today, campuses=()):
        from products.cyed.admissions.models import Application, Offer

        made = 0
        for i, (first, last, year, status, source) in enumerate(APPLICANTS):
            campus = campuses[i % len(campuses)] if campuses else None
            app, created = Application.objects.get_or_create(
                tenant_id=tenant, applicant_first_name=first, applicant_last_name=last,
                defaults=dict(
                    year_level_applying=year, status=status, source=source, campus=campus,
                    date_of_birth=date(2026 - year - 5, 3, 12),
                    guardian_name=f"{first}'s parent", guardian_email=f"{last.lower()}@example.com",
                    guardian_phone="0400 000 000",
                    residential_suburb="Parramatta", residential_postcode="2150",
                ),
            )
            made += int(created)
            if status in ("offer", "accepted") :
                Offer.objects.get_or_create(
                    tenant_id=tenant, application=app,
                    defaults=dict(
                        offered_year_level=year, offer_date=today - timedelta(days=10),
                        expiry_date=today + timedelta(days=11),
                        response="accepted" if status == "accepted" else "pending",
                        conditions="Subject to receipt of the enrolment deposit.",
                    ),
                )
        return {"applications": made}

    def _notices(self, tenant, staff, today, campuses=()):
        from products.cyed.school.models import Notice

        made = 0
        author = f"{staff[0].first_name} {staff[0].last_name}" if staff else "Front office"
        for title, body, audience, priority in NOTICES:
            _, created = Notice.objects.get_or_create(
                tenant_id=tenant, title=title,
                defaults=dict(body=body, audience=audience, priority=priority,
                              starts_on=today, ends_on=today + timedelta(days=7),
                              is_published=True, posted_by=author),
            )
            made += int(created)

        # One notice belonging to each site. A group that can only publish
        # group-wide notices cannot run four schools — the campus filter has to
        # have something to filter.
        for campus in campuses:
            _, created = Notice.objects.get_or_create(
                tenant_id=tenant, title=f"{campus.name} — assembly Thursday",
                defaults=dict(
                    body=(
                        f"{campus.name} assembly runs Thursday period 3 in the hall. "
                        "Year advisers to collect their cohort from the quad."
                    ),
                    audience="all", priority="normal", campus=campus,
                    starts_on=today, ends_on=today + timedelta(days=5),
                    is_published=True, posted_by=author,
                ),
            )
            made += int(created)
        return {"notices": made}

    def _health(self, tenant, students, today):
        from products.cyed.health.models import HealthRecord, ImmunisationRecord

        records = immunisations = 0
        allergies = ["Peanuts, tree nuts", "", "Bee stings", "", "Dairy", ""]
        for i, student in enumerate(students):
            _, created = HealthRecord.objects.get_or_create(
                tenant_id=tenant, student=student,
                defaults=dict(
                    allergies=allergies[i % len(allergies)],
                    conditions="Asthma — reliever in the sick bay" if i % 7 == 0 else "",
                    dietary_requirements="Halal" if i % 9 == 0 else "",
                    emergency_contact="Listed guardian",
                ),
            )
            records += int(created)
            # A realistic spread: most up to date, a few chasing paperwork.
            status = ("up_to_date", "up_to_date", "up_to_date", "catch_up",
                      "not_provided", "medical_exemption")[i % 6]
            # Sighted and verified for the compliant majority. Without a
            # verification date *every* record counts as a gap, so a school
            # with a healthy register would open this screen to a list of its
            # entire enrolment and conclude the report is broken.
            verified = status in ("up_to_date", "catch_up", "medical_exemption")
            _, created = ImmunisationRecord.objects.get_or_create(
                tenant_id=tenant, student=student,
                defaults=dict(
                    status=status,
                    air_statement_on=today - timedelta(days=120) if verified else None,
                    verified_on=today - timedelta(days=100) if verified else None,
                    verified_by="registrar@cyed.edu.au" if verified else "",
                    exemption_reason="Immunosuppressed — GP letter on file" if status == "medical_exemption" else "",
                ),
            )
            immunisations += int(created)
        return {"health records": records, "immunisation records": immunisations}

    def _wellbeing(self, tenant, students, staff, today):
        from products.cyed.wellbeing.models import BehaviourIncident

        made = 0
        reporter = f"{staff[0].first_name} {staff[0].last_name}" if staff else "Staff"
        # Spread across the last 12 weeks so the leadership behaviour chart has
        # a shape rather than a single spike, and weighted positive — a school
        # that only records incidents reads as though it is getting worse.
        for week in range(12):
            when = today - timedelta(weeks=week, days=random.randint(0, 4))
            per_week = max(3, min(len(students) // 25, 40))
            for _ in range(random.randint(per_week, per_week * 2)):
                student = random.choice(students)
                roll = random.random()
                if roll < 0.6:
                    category, desc, points = "positive", random.choice(POSITIVE), 5
                elif roll < 0.9:
                    category, desc, points = "minor", random.choice(MINOR), -2
                else:
                    category, desc, points = "major", random.choice(MAJOR), -10
                _, created = BehaviourIncident.objects.get_or_create(
                    tenant_id=tenant, student=student, date=when, description=desc,
                    defaults=dict(category=category, points=points, reported_by=reporter,
                                  action_taken="Spoken with student." if points < 0 else "",
                                  resolved=points >= 0),
                )
                made += int(created)
        return {"behaviour incidents": made}

    def _messaging(self, tenant, students, staff):
        from products.cyed.messaging.models import Message, MessageThread, ThreadParticipant

        if not staff:
            return {"message threads": 0}
        teacher = staff[0]
        teacher_email = teacher.email or "teacher@cyed.edu.au"
        made = 0
        conversations = [
            ("Reading progress this term", "teacher_parent",
             "Just a note that your child's reading has come along well this term — the extra practice at home is showing.",
             "Thank you, that is good to hear. We will keep it up."),
            ("Absence on Thursday", "office_parent",
             "We have your child marked absent on Thursday with no explanation. Could you let us know?",
             "Sorry — dental appointment. I have submitted the explanation in the portal."),
            ("Camp payment arrangement", "office_parent",
             "You asked about paying the camp fee in two parts. That is fine — the office can set it up.",
             "That would help a lot, thank you."),
        ]
        for i, (subject, kind, first, reply) in enumerate(conversations):
            student = students[i % len(students)]
            guardian = student.guardians.first()
            guardian_email = guardian.email if guardian else "parent@example.com"
            thread, created = MessageThread.objects.get_or_create(
                tenant_id=tenant, subject=subject,
                defaults=dict(kind=kind, student=student, opened_by_email=teacher_email),
            )
            if created:
                made += 1
                # Participants decide visibility — a thread without them is
                # readable by nobody, so the family would never see it in their
                # portal and staff would only ever be "observing" it.
                ThreadParticipant.objects.create(
                    tenant_id=tenant, thread=thread, party_kind="staff",
                    email=teacher_email,
                    display_name=f"{teacher.first_name} {teacher.last_name}",
                    staff=teacher, last_read_at=timezone.now(),
                )
                if guardian:
                    ThreadParticipant.objects.create(
                        tenant_id=tenant, thread=thread, party_kind="guardian",
                        email=guardian_email,
                        display_name=f"{guardian.first_name} {guardian.last_name}".strip(),
                        guardian=guardian, student=student,
                    )

                # Explicit, separated timestamps: written in one loop they land
                # in the same millisecond, and "last message" then depends on
                # insertion order rather than on time.
                opened = timezone.now() - timedelta(days=2 + i)
                Message.objects.create(
                    tenant_id=tenant, thread=thread, sender_kind="staff",
                    sender_email=teacher_email,
                    sender_name=f"{teacher.first_name} {teacher.last_name}", body=first,
                    sent_at=opened,
                )
                answered = opened + timedelta(hours=3)
                Message.objects.create(
                    tenant_id=tenant, thread=thread, sender_kind="guardian",
                    sender_email=guardian_email,
                    sender_name=guardian.first_name if guardian else "Parent", body=reply,
                    sent_at=answered,
                )
                thread.last_message_at = answered
                thread.save(update_fields=["last_message_at"])
        return {"message threads": made}

    def _lms(self, tenant, sections):
        from products.cyed.lms.models import Course, Lesson, Module

        made = lessons = 0
        # One per section across every campus — matching on name alone merged
        # "10A Mathematics" at four different schools into a single course.
        for section in sections[:40]:
            course, created = Course.objects.get_or_create(
                tenant_id=tenant, class_section=section,
                name=f"{section.name} — {section.campus.code if section.campus else 'Group'}",
                defaults=dict(subject=section.subject or "General", year_level=section.year_level,
                              is_published=True,
                              description="Term unit built from the Australian Curriculum."),
            )
            made += int(created)
            module, _ = Module.objects.get_or_create(
                tenant_id=tenant, course=course, name="Unit 1 — Foundations",
                defaults=dict(sequence=1, description="Core concepts for the term."),
            )
            for n, title in enumerate(["Getting started", "Key ideas", "Applying it", "Review"], start=1):
                _, created = Lesson.objects.get_or_create(
                    tenant_id=tenant, module=module, title=title,
                    defaults=dict(sequence=n, estimated_minutes=50, is_published=True,
                                  content=f"{title}: teacher notes and student activity for this lesson."),
                )
                lessons += int(created)
        return {"courses": made, "lessons": lessons}

    def _assessment(self, tenant, sections, today):
        from products.cyed.assessment.models import Assignment

        made = 0
        for i, section in enumerate(sections[:40]):
            _, created = Assignment.objects.get_or_create(
                tenant_id=tenant, class_section=section, title=f"{section.name} — Research task",
                defaults=dict(
                    instructions="Research the topic set in class and submit 600 words.",
                    due_at=timezone.now() + timedelta(days=7 - i),
                    max_score=Decimal("30.00"), allow_late=i % 2 == 0, is_published=True,
                ),
            )
            made += int(created)
        return {"assignments": made}

    def _hr(self, tenant, staff, today):
        from products.cyed.hr.models import PerformanceReview, StaffLeave

        leave = reviews = 0
        for i, member in enumerate(staff[: min(len(staff), 20)]):
            start = today + timedelta(days=(i * 5) - 10)
            _, created = StaffLeave.objects.get_or_create(
                tenant_id=tenant, staff=member, start_date=start,
                defaults=dict(
                    leave_type=("annual", "sick", "long_service", "annual", "unpaid", "parental")[i % 6],
                    end_date=start + timedelta(days=2), days=Decimal("3"),
                    status=("approved", "requested", "approved", "rejected", "requested", "approved")[i % 6],
                    reason="Family commitment.",
                ),
            )
            leave += int(created)
            _, created = PerformanceReview.objects.get_or_create(
                tenant_id=tenant, staff=member, review_period="2026 Semester 1",
                defaults=dict(
                    review_date=today - timedelta(days=30), reviewer_name="Principal",
                    overall_rating=(4, 5, 3, 4, 5, 4)[i % 6],
                    strengths="Strong classroom practice and good rapport with families.",
                    development_areas="Data literacy — using assessment data to plan.",
                    goals="Lead one moderation session next semester.",
                    status=("acknowledged", "submitted", "draft", "acknowledged", "closed", "submitted")[i % 6],
                ),
            )
            reviews += int(created)
        return {"staff leave": leave, "performance reviews": reviews}

    def _procurement(self, tenant):
        from products.cyed.procurement.models import PurchaseOrder, PurchaseOrderLine, Supplier

        suppliers = []
        for name, abn, email in SUPPLIERS:
            supplier, _ = Supplier.objects.get_or_create(
                tenant_id=tenant, name=name,
                defaults=dict(abn=abn, email=email, phone="02 9000 0000", is_active=True),
            )
            suppliers.append(supplier)

        orders = 0
        # Left at draft/ordered deliberately: receiving posts Dr Inventory /
        # Cr Accounts Payable, and seeded journal entries would put the demo's
        # trial balance at odds with its own purchase history.
        for i, supplier in enumerate(suppliers):
            po, created = PurchaseOrder.objects.get_or_create(
                tenant_id=tenant, supplier=supplier, reference=f"PO-2026-{100 + i}",
                defaults=dict(status="ordered" if i else "draft", order_date=timezone.localdate()),
            )
            if created:
                orders += 1
                PurchaseOrderLine.objects.create(
                    tenant_id=tenant, purchase_order=po,
                    description="A4 copy paper — 20 boxes", quantity=20,
                    unit_price=Decimal("42.50"),
                )
                PurchaseOrderLine.objects.create(
                    tenant_id=tenant, purchase_order=po,
                    description="Whiteboard markers — 30 packs", quantity=30,
                    unit_price=Decimal("8.90"),
                )
        return {"suppliers": len(suppliers), "purchase orders": orders}

    def _inventory_assets(self, tenant, today):
        from products.cyed.assets.models import Asset
        from products.cyed.inventory.models import InventoryItem

        items = 0
        for name, sku, category, unit, on_hand, reorder, location in INVENTORY:
            _, created = InventoryItem.objects.get_or_create(
                tenant_id=tenant, sku=sku,
                defaults=dict(name=name, category=category, unit=unit, on_hand=on_hand,
                              reorder_level=reorder, location=location),
            )
            items += int(created)

        assets = 0
        for name, tag, category, location, cost, life in ASSETS:
            _, created = Asset.objects.get_or_create(
                tenant_id=tenant, asset_tag=tag,
                defaults=dict(name=name, category=category, location=location,
                              acquisition_date=today - timedelta(days=400),
                              acquisition_cost=Decimal(cost), useful_life_years=life,
                              status="in_use"),
            )
            assets += int(created)
        return {"inventory items": items, "assets": assets}

    def _transport(self, tenant, students):
        from products.cyed.transport.models import Bus, TransportSubscription, TransportZone

        zones = []
        for name, lo, hi, fee in [("Zone A", 0, 5, "600.00"), ("Zone B", 5, 12, "900.00"),
                                  ("Zone C", 12, 25, "1200.00")]:
            zone, _ = TransportZone.objects.get_or_create(
                tenant_id=tenant, name=name,
                defaults=dict(min_km=lo, max_km=hi, base_fee=Decimal(fee), is_active=True),
            )
            zones.append(zone)

        buses = []
        for ident, rego, driver in [("Bus 1", "AB 12 CD", "Ray Mitchell"),
                                    ("Bus 2", "EF 34 GH", "Sandra Ng")]:
            bus, _ = Bus.objects.get_or_create(
                tenant_id=tenant, identifier=ident,
                defaults=dict(rego=rego, make_model="Toyota Coaster", capacity=22,
                              driver_name=driver, supervisor_name="Rostered staff", is_active=True),
            )
            buses.append(bus)

        subs = 0
        for i, student in enumerate(students[: max(10, min(len(students) // 7, 300))]):
            _, created = TransportSubscription.objects.get_or_create(
                tenant_id=tenant, student=student,
                defaults=dict(zone=zones[i % len(zones)], assigned_bus=buses[i % len(buses)],
                              trip_type="full_trip" if i % 3 else "half_morning",
                              pickup_address=f"{10 + i} Station Street, Parramatta",
                              status="active", start_date=timezone.localdate() - timedelta(days=60)),
            )
            subs += int(created)
        return {"transport subscriptions": subs}

    def _visitors(self, tenant, staff):
        from products.cyed.visitors.models import Visitor

        host = f"{staff[0].first_name} {staff[0].last_name}" if staff else "Front office"
        made = 0
        people = [
            ("Dr Helen Fraser", "Speech Pathology NSW", "Student assessment", True, False),
            ("Marcus Webb", "Fire & Rescue NSW", "Annual extinguisher service", False, True),
            ("Priya Raman", "Parent", "Volunteer — reading group", True, False),
        ]
        for name, org, purpose, wwc, signed_out in people:
            visitor, created = Visitor.objects.get_or_create(
                tenant_id=tenant, full_name=name,
                defaults=dict(organisation=org, purpose=purpose, host_name=host,
                              badge_no=f"V{random.randint(100, 999)}", wwc_verified=wwc,
                              # Set explicitly: the viewset stamps this on create,
                              # but seeding writes the model directly, and a
                              # visitor with no sign-in time is never "on site" —
                              # which is the only list this register is read for.
                              signed_in_at=timezone.now() - timedelta(hours=2),
                              signed_out_at=timezone.now() if signed_out else None),
            )
            made += int(created)
        return {"visitors": made}

    def _reports(self, tenant, students, sections):
        from products.cyed.reporting.models import ReportCard, ReportCardEntry

        subjects = ["English", "Mathematics", "Science", "HASS", "Health and PE"]
        made = 0
        for student in students[: max(8, min(len(students) // 4, 300))]:
            card, created = ReportCard.objects.get_or_create(
                tenant_id=tenant, student=student, term="Semester 1",
                defaults=dict(status="draft",
                              general_comment="A settled semester with steady progress across subjects."),
            )
            if created:
                made += 1
                for subject in subjects:
                    ReportCardEntry.objects.create(
                        tenant_id=tenant, report_card=card, subject=subject,
                        achievement=random.choice("ABBCCD"),
                        effort=random.choice(["high", "consistent", "consistent", "developing"]),
                        comment=f"{subject}: works steadily and contributes to class discussion.",
                        teacher_name="Class teacher",
                    )
        return {"report cards (draft)": made}

    def _relief(self, tenant, today, campuses=()):
        from products.cyed.substitution.models import ReliefTeacher

        made = 0
        people = [
            ("Jane", "Alderton", "Primary, English", "active"),
            ("Peter", "Nsubuga", "Mathematics, Science", "active"),
            ("Wendy", "Cho", "The Arts", "inactive"),
        ]
        for i, (first, last, subjects, status) in enumerate(people):
            campus = campuses[i % len(campuses)] if campuses else None
            _, created = ReliefTeacher.objects.get_or_create(
                tenant_id=tenant, first_name=first, last_name=last,
                defaults=dict(
                    campus=campus,
                    email=f"{first.lower()}.{last.lower()}@relief.example", phone="0400 111 222",
                    agency="ClassCover", subjects=subjects, daily_rate=Decimal("420.00"),
                    half_day_rate=Decimal("240.00"), status=status,
                    wwcc_number=f"WWC{random.randint(100000, 999999)}E",
                    wwcc_expires_on=today + timedelta(days=365),
                    registration_number=f"NESA{random.randint(10000, 99999)}",
                    registration_expires_on=today + timedelta(days=200),
                    verified_by="Front office", verified_on=today - timedelta(days=30),
                ),
            )
            made += int(created)
        return {"relief teachers": made}

    def _interviews(self, tenant, staff, today):
        from products.cyed.meetings.models import InterviewRound, InterviewSlot

        if not staff:
            return {"interview slots": 0}
        round_, created = InterviewRound.objects.get_or_create(
            tenant_id=tenant, name="Semester 1 parent–teacher interviews",
            defaults=dict(
                bookings_open_at=timezone.now() - timedelta(days=2),
                bookings_close_at=timezone.now() + timedelta(days=12),
                max_bookings_per_student=4, is_published=True,
                instructions="Interviews run for ten minutes. Please arrive five minutes early.",
            ),
        )
        slots = 0
        if created:
            evening = timezone.now().replace(hour=16, minute=0, second=0, microsecond=0)
            evening += timedelta(days=14)
            for member in staff[:4]:
                for n in range(8):
                    InterviewSlot.objects.create(
                        tenant_id=tenant, round=round_, teacher=member,
                        starts_at=evening + timedelta(minutes=10 * n),
                        duration_minutes=10, location=f"Hall table {staff.index(member) + 1}",
                        is_available=True,
                    )
                    slots += 1
        return {"interview slots": slots}

    def _exams(self, tenant, students, today, campuses=()):
        from products.cyed.exams.models import ExamCandidate, ExamRoom, ExamSitting

        # A hall per site: exam rooms are physical places, and a group sitting
        # the same paper still seats it four times.
        main = campuses[0] if campuses else None
        for campus in campuses[1:]:
            ExamRoom.objects.get_or_create(
                tenant_id=tenant, name=f"{campus.name} Hall",
                defaults=dict(code=f"{(campus.code or 'C')[:6]}H", capacity=120,
                              rows=10, columns=12, campus=campus, is_accessible=True),
            )
        room, _ = ExamRoom.objects.get_or_create(
            tenant_id=tenant, name="Main Hall",
            defaults=dict(code="HALL", capacity=120, rows=10, columns=12,
                          campus=main, is_accessible=True),
        )
        quiet, _ = ExamRoom.objects.get_or_create(
            tenant_id=tenant, name="Room 4 — separate supervision",
            defaults=dict(code="R4", capacity=6, rows=2, columns=3,
                          campus=main, is_accessible=True),
        )
        sitting, created = ExamSitting.objects.get_or_create(
            tenant_id=tenant, name="Year 10 Mathematics — Semester 1 exam",
            defaults=dict(subject="Mathematics", year_level=10, date=today + timedelta(days=21),
                          duration_minutes=90, status="planned",
                          materials_permitted="Scientific calculator, blue or black pen.",
                          instructions="No phones or smart watches in the exam room."),
        )
        candidates = 0
        if created:
            year10 = [s for s in students if s.year_level == 10] or students[:8]
            for i, student in enumerate(year10):
                # One candidate with an access arrangement, because provisions
                # are the part of exam management schools get audited on.
                arrangement = "extra_time" if i == 0 else ""
                ExamCandidate.objects.create(
                    tenant_id=tenant, sitting=sitting, student=student,
                    room=quiet if i == 0 else room,
                    seat_label=f"{chr(65 + i // 12)}{i % 12 + 1}",
                    access_arrangement=arrangement,
                    extra_time_minutes=15 if arrangement else 0,
                    attendance="expected",
                )
                candidates += 1
        return {"exam candidates": candidates}

    def _learner_profiles(self, tenant, students, today):
        """
        The profiles the adaptive AI reads. Without them every AI feature in the
        demo behaves as though every child is identical, which is the opposite
        of the point being made.
        """
        from products.cyed.wellbeing.models import LearnerProfile, WellbeingCheckIn

        profiles = checkins = 0
        languages = ["Arabic", "Vietnamese", "Mandarin", "Hindi", "Greek"]
        for i, student in enumerate(students):
            eald = ("", "", "", "DV", "CO", "EM")[i % 6]
            _, created = LearnerProfile.objects.get_or_create(
                tenant_id=tenant, student=student,
                defaults=dict(
                    eald_level=eald,
                    first_language=languages[i % len(languages)] if eald else "English",
                    is_neurodivergent=i % 7 == 0,
                    accommodations=("Chunked instructions; movement break each lesson."
                                    if i % 7 == 0 else ""),
                    reading_level=f"Level {8 + (i % 5)}",
                    has_individual_plan=i % 11 == 0,
                ),
            )
            profiles += int(created)

        # A fortnight of check-ins over a slice of the cohort — enough for the
        # cohort view to have a distribution, including a couple of low moods,
        # since a wellbeing screen where everyone is fine tests nothing.
        moods = ["great", "ok", "ok", "ok", "low", "struggling"]
        for i, student in enumerate(students[: max(12, min(len(students) // 8, 150))]):
            for day_offset in (1, 4, 8):
                when = today - timedelta(days=day_offset)
                mood = moods[(i + day_offset) % len(moods)]
                _, created = WellbeingCheckIn.objects.get_or_create(
                    tenant_id=tenant, student=student, date=when,
                    defaults=dict(
                        mood=mood,
                        response_text={
                            "great": "Good week, enjoyed the science prac.",
                            "ok": "Fine. Busy with assignments.",
                            "low": "Tired and a bit behind on work.",
                            "struggling": "Finding it hard to keep up and not sleeping well.",
                        }[mood],
                    ),
                )
                checkins += int(created)
        return {"learner profiles": profiles, "wellbeing check-ins": checkins}

    def _payroll_and_attendance(self, tenant, staff, today):
        from products.cyed.payroll.models import PayrollRun
        from products.cyed.staff_attendance.models import StaffAttendanceDay

        runs = 0
        for months_back in (2, 1):
            start = (today.replace(day=1) - timedelta(days=months_back * 30)).replace(day=1)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            _, created = PayrollRun.objects.get_or_create(
                tenant_id=tenant, period_label=start.strftime("%B %Y"),
                defaults=dict(period_start=start, period_end=end,
                              pay_date=end + timedelta(days=3), status="draft"),
            )
            runs += int(created)

        days = 0
        # Two working weeks, including lateness — the drift between attendance
        # and payroll is what the reconcile action exists to surface.
        for member in staff[:40]:
            for back in range(1, 15):
                day = today - timedelta(days=back)
                if day.weekday() >= 5:
                    continue
                late = (hash((str(member.id), day.toordinal())) % 11) == 0
                _, created = StaffAttendanceDay.objects.get_or_create(
                    tenant_id=tenant, staff=member, date=day,
                    defaults=dict(status="late" if late else "present",
                                  minutes_late=12 if late else 0,
                                  hours_worked=Decimal("7.50")),
                )
                days += int(created)
        return {"payroll runs (draft)": runs, "staff attendance days": days}

    def _docsign(self, tenant, staff, students, today):
        from products.cyed.docsign.models import SignableDocument, Signatory

        made = 0
        if staff:
            doc, created = SignableDocument.objects.get_or_create(
                tenant_id=tenant, title="Casual teaching agreement — Term 3",
                defaults=dict(doc_type="staff_contract", staff=staff[0],
                              body="Agreement to undertake casual teaching duties for Term 3.",
                              status="draft", created_by="Front office",
                              due_date=today + timedelta(days=14)),
            )
            if created:
                made += 1
                Signatory.objects.create(
                    tenant_id=tenant, document=doc,
                    name=f"{staff[0].first_name} {staff[0].last_name}",
                    email=staff[0].email or "staff@cyed.edu.au", role="staff", order=1,
                )

        if students:
            student = students[0]
            guardian = student.guardians.first()
            doc, created = SignableDocument.objects.get_or_create(
                tenant_id=tenant, title="Excursion permission — Marine Biology Field Trip",
                defaults=dict(doc_type="permission_slip", student=student,
                              body="Permission for your child to attend the Year 9 marine "
                                   "biology field trip, including travel by chartered bus.",
                              status="draft", created_by="Front office",
                              due_date=today + timedelta(days=7)),
            )
            if created:
                made += 1
                Signatory.objects.create(
                    tenant_id=tenant, document=doc,
                    name=f"{guardian.first_name} {guardian.last_name}" if guardian else "Parent",
                    email=guardian.email if guardian else "parent@example.com",
                    role="parent", order=1,
                )
        return {"signable documents": made}

    def _nccd(self, tenant, students, today):
        """
        The statutory NCCD return reads `compliance.NCCDRecord`, which is a
        separate store from the adjustments recorded on a support plan — the
        plan is the school's working document, this is what gets lodged. Seeded
        so the return is not empty on a demo instance, where "0 rows" reads as
        a broken export rather than a school with no students on adjustments.
        """
        from products.cyed.compliance.models import NCCDRecord

        made = 0
        spread = [
            ("cognitive", "supplementary"),
            ("social_emotional", "substantial"),
            ("physical", "qdtp"),
            ("sensory", "extensive"),
            ("cognitive", "qdtp"),
            ("social_emotional", "supplementary"),
        ]
        # Around 1 student in 20 is reported nationally; keep that ratio so
        # the return is plausible to anyone who lodges one.
        for i, student in enumerate(students[: max(6, len(students) // 20)]):
            category, level = spread[i % len(spread)]
            _, created = NCCDRecord.objects.get_or_create(
                tenant_id=tenant, student=student, collection_year=today.year,
                defaults=dict(
                    category=category, level_of_adjustment=level,
                    imputed_disability=i % 3 == 0,
                    evidence_note=(
                        "Adjustments documented in the student's plan; family consulted "
                        "and teacher observations retained."
                    ),
                ),
            )
            made += int(created)
        return {"nccd records": made}
