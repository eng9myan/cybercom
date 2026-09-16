"""
CyEd domain data → SIF AU v3.x object shapes.

Each mapper returns plain dicts (the encoders turn them into XML or JSON) and
declares a `GAPS` list naming the SIF elements CyEd cannot populate and why.

The gap lists are the honest part and are not decoration. A consumer that
receives a `StudentPersonal` with no `LocalId` cannot match it to their own
record, and finding that out from a failed load is much worse than reading it
in a coverage report first. Every gap here is a real one — none are aspirational
"coming soon" entries.
"""

from products.cyed.sif.refids import get_or_create_refid, synthetic_local_id

# SIF AU data model namespace.
SIF_AU_NAMESPACE = "http://www.sifassociation.org/au/datamodel/3.4"


def _name_type(family, given, preferred=""):
    """SIF `NameType`. `LGL` is the legal-name type code."""
    name = {"@Type": "LGL", "FamilyName": family or "", "GivenName": given or ""}
    if preferred:
        name["PreferredGivenName"] = preferred
    return name


def _sif_date(value):
    return value.isoformat() if value else None


# ── StudentPersonal ──────────────────────────────────────────────────────────
STUDENT_PERSONAL_GAPS = [
    {
        "element": "PersonInfo/AddressList",
        "reason": (
            "CyEd stores the home address on the household (sis.Family), not the "
            "student, and does not model SIF AddressType sub-elements "
            "(Street/Line1, City, StateProvince, PostalCode) separately."
        ),
    },
    {
        "element": "MostRecent/Homegroup",
        "reason": "CyEd has ClassSection but no distinct homegroup/roll-class concept.",
    },
    {
        "element": "PersonInfo/Demographics/BirthDate precision",
        "reason": "Date of birth is optional in CyEd and may be absent for imported rows.",
    },
    {
        "element": "EducationSupport / DisabilityLevelOfAdjustment",
        "reason": (
            "NCCD adjustment level lives in the compliance app's export and is not "
            "surfaced on the student object."
        ),
    },
    {
        "element": "Demographics/LBOTE",
        "reason": (
            "CyEd holds LBOTE as its own boolean. SIF derives it from LanguageList "
            "with jurisdictional language codes, and CyEd stores the home language "
            "as free text rather than a coded value, so the derivation cannot be "
            "reproduced faithfully."
        ),
    },
]


def student_personal(student):
    refid = get_or_create_refid(
        student.tenant_id, "StudentPersonal", student.id,
        description=f"Student {student.first_name} {student.last_name}",
    )
    return {
        "@RefId": str(refid),
        "LocalId": student.student_number or str(student.id),
        "StateProvinceId": student.state_student_number or None,
        "ElectronicIdList": (
            {"ElectronicId": [{"@Type": "USI", "#text": student.usi}]} if student.usi else None
        ),
        "PersonInfo": {
            "Name": _name_type(student.last_name, student.first_name),
            "Demographics": {
                "IndigenousStatus": student.indigenous_status or "9",
                "Sex": student.gender or None,
                "BirthDate": _sif_date(student.date_of_birth),
                "CountryOfBirth": student.country_of_birth or None,
                "LanguageList": (
                    {"Language": [{"Code": student.language_at_home, "LanguageType": "4"}]}
                    if student.language_at_home else None
                ),
            },
            "EmailList": (
                {"Email": [{"@Type": "01", "#text": student.email}]} if student.email else None
            ),
        },
        "MostRecent": {
            "YearLevel": {"Code": _year_level_code(student.year_level)},
            "SchoolLocalId": _campus_local_id(student),
        },
        "EnrollmentStatus": _enrollment_status(student.enrolment_status),
    }


def _year_level_code(year_level) -> str:
    """SIF AU uses 'F' for Foundation; CyEd stores it as 0."""
    if year_level in (0, None):
        return "F"
    return str(year_level)


def _campus_local_id(student):
    return getattr(student.campus, "code", None) or (
        str(student.campus_id) if student.campus_id else None
    )


def _enrollment_status(status) -> str:
    """SIF enrollment status codes: A=active, I=inactive."""
    return "A" if status == "enrolled" else "I"


# ── StaffPersonal ────────────────────────────────────────────────────────────
STAFF_PERSONAL_GAPS = [
    {
        "element": "PersonInfo/AddressList",
        "reason": "CyEd does not store staff home addresses.",
    },
    {
        "element": "OtherIdList/TeacherRegistrationNumber",
        "reason": (
            "Teacher registration is held as an hr.StaffClearance row and is not "
            "yet emitted as a SIF OtherId; the mapping to jurisdictional id types "
            "(VIT/NESA/TRB) has not been agreed."
        ),
    },
    {
        "element": "StaffPersonal/EmploymentDetails",
        "reason": "Contract data exists in hr.Contract but the SIF employment sub-object is unmapped.",
    },
]


def staff_personal(staff):
    refid = get_or_create_refid(
        staff.tenant_id, "StaffPersonal", staff.id,
        description=f"Staff {staff.first_name} {staff.last_name}",
    )
    return {
        "@RefId": str(refid),
        "LocalId": staff.staff_number or str(staff.id),
        "PersonInfo": {
            "Name": _name_type(staff.last_name, staff.first_name),
            "EmailList": (
                {"Email": [{"@Type": "01", "#text": staff.email}]} if staff.email else None
            ),
            "PhoneNumberList": (
                {"PhoneNumber": [{"@Type": "0096", "Number": staff.phone}]}
                if staff.phone else None
            ),
        },
        "SchoolLocalId": getattr(staff.campus, "code", None) or None,
        "StaffStatus": "A" if staff.is_active else "I",
    }


# ── SchoolInfo ───────────────────────────────────────────────────────────────
SCHOOL_INFO_GAPS = [
    {
        "element": "ACARAId",
        "reason": (
            "CyEd has no ACARA School ID field, so its output cannot be matched to "
            "My School. This also blocks ICSEA-based reporting."
        ),
    },
    {
        "element": "SchoolFocusList / SchoolSector / OperationalStatus",
        "reason": "Not modelled on org.Campus.",
    },
    {
        "element": "AddressList",
        "reason": "Campus addresses are free text, not SIF AddressType sub-elements.",
    },
]


def school_info(campus):
    refid = get_or_create_refid(
        campus.tenant_id, "SchoolInfo", campus.id, description=f"Campus {campus.name}",
    )
    return {
        "@RefId": str(refid),
        "LocalId": campus.code or str(campus.id),
        "SchoolName": campus.name,
        "SchoolType": None,
        "ACARAId": None,   # see SCHOOL_INFO_GAPS
        "OperationalStatus": "A" if getattr(campus, "is_active", True) else "I",
    }


# ── StudentSchoolEnrollment ──────────────────────────────────────────────────
STUDENT_ENROLLMENT_GAPS = [
    {
        "element": "MembershipType / TimeFrame",
        "reason": (
            "CyEd records enrolment status but not SIF membership type (home-school "
            "vs concurrent) or historical/future time frames."
        ),
    },
    {
        "element": "FTE",
        "reason": "Student FTE is not modelled; all students are assumed full-time.",
    },
    {
        "element": "Entry/ExitType codes",
        "reason": (
            "Exit reason is free text on the student record, not a jurisdictional "
            "exit-type code."
        ),
    },
]


def student_school_enrollment(student):
    """
    Derived: a student's standing at their school. No single row backs it, so
    the local id is a deterministic hash of the parts.
    """
    local_id = synthetic_local_id(
        "StudentSchoolEnrollment", student.id, student.campus_id
    )
    refid = get_or_create_refid(
        student.tenant_id, "StudentSchoolEnrollment", local_id,
        source_local_id=student.id,
        description=f"Enrollment of student {student.id}",
    )
    return {
        "@RefId": str(refid),
        "StudentPersonalRefId": str(
            get_or_create_refid(student.tenant_id, "StudentPersonal", student.id)
        ),
        "SchoolLocalId": _campus_local_id(student),
        "MembershipType": None,   # see STUDENT_ENROLLMENT_GAPS
        "TimeFrame": "Current" if student.enrolment_status == "enrolled" else "Historical",
        "YearLevel": {"Code": _year_level_code(student.year_level)},
        "Entry": None,
        "Exit": (
            {"ExitDate": _sif_date(student.exit_date), "ExitStatus": student.exit_reason or None}
            if student.exit_date else None
        ),
        "FTE": None,
    }


# ── StudentAttendance ────────────────────────────────────────────────────────
STUDENT_ATTENDANCE_GAPS = [
    {
        "element": "AttendanceCode (jurisdictional)",
        "reason": (
            "CyEd's statuses (present/absent/late/excused/left_early) are mapped to "
            "generic SIF day values. Jurisdiction-specific attendance codes have not "
            "been agreed and differ per state."
        ),
    },
    {
        "element": "SessionInfoList",
        "reason": (
            "Per-period marks exist in CyEd but are collapsed to a daily figure here; "
            "SIF session-level reporting is unmapped."
        ),
    },
    {
        "element": "AttendanceTimes",
        "reason": "Arrival/departure times are not recorded, only minutes-late on a mark.",
    },
]

# CyEd status → SIF daily attendance value.
_ATTENDANCE_VALUE = {
    "present": "100",       # full day present
    "absent": "000",        # full day absent
    "late": "100",          # present, arrived late
    "excused": "000",
    "left_early": "050",    # partial
}


def student_attendance(mark):
    """Derived: one student's attendance on one day."""
    day = getattr(mark.roll_call, "date", None)
    local_id = synthetic_local_id("StudentAttendance", mark.student_id, day)
    refid = get_or_create_refid(
        mark.tenant_id, "StudentAttendance", local_id,
        source_local_id=mark.id,
        description=f"Attendance for student {mark.student_id} on {day}",
    )
    return {
        "@RefId": str(refid),
        "StudentPersonalRefId": str(
            get_or_create_refid(mark.tenant_id, "StudentPersonal", mark.student_id)
        ),
        "SchoolLocalId": _campus_local_id(mark.student),
        "Date": _sif_date(day),
        "AttendanceCode": {
            "CodeSet": "Local",
            "Code": mark.status,
            "OtherCodeList": {"OtherCode": [{"@Codeset": "Text", "#text": mark.get_status_display()}]},
        },
        "DailyAttendanceValue": _ATTENDANCE_VALUE.get(mark.status, "000"),
        "AttendanceNote": mark.note or None,
    }


# ── registry ─────────────────────────────────────────────────────────────────
OBJECTS = {
    "StudentPersonal": {
        "mapper": student_personal,
        "gaps": STUDENT_PERSONAL_GAPS,
        "collection": "StudentPersonals",
    },
    "StaffPersonal": {
        "mapper": staff_personal,
        "gaps": STAFF_PERSONAL_GAPS,
        "collection": "StaffPersonals",
    },
    "SchoolInfo": {
        "mapper": school_info,
        "gaps": SCHOOL_INFO_GAPS,
        "collection": "SchoolInfos",
    },
    "StudentSchoolEnrollment": {
        "mapper": student_school_enrollment,
        "gaps": STUDENT_ENROLLMENT_GAPS,
        "collection": "StudentSchoolEnrollments",
    },
    "StudentAttendance": {
        "mapper": student_attendance,
        "gaps": STUDENT_ATTENDANCE_GAPS,
        "collection": "StudentAttendances",
    },
}
