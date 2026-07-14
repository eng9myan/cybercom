from django.db import models

from platform.common.models import BaseModel

PRODUCT_AREA_CHOICES = [
    ("cymed", "CyMed"),
    ("cycom", "CyCom"),
    ("cygov", "CyGov"),
    ("cycitizen", "CyCitizen"),
    ("cyai", "CyAI"),
    ("cyconnect", "CyConnect"),
    ("platform", "Platform"),
    ("all", "All Products"),
]

TARGET_AUDIENCE_CHOICES = [
    ("end_user", "End User"),
    ("administrator", "Administrator"),
    ("developer", "Developer"),
    ("architect", "Architect"),
    ("partner", "Partner"),
]

COURSE_LEVEL_CHOICES = [
    ("beginner", "Beginner"),
    ("intermediate", "Intermediate"),
    ("advanced", "Advanced"),
    ("expert", "Expert"),
]

CONTENT_TYPE_CHOICES = [
    ("video", "Video"),
    ("document", "Document"),
    ("quiz", "Quiz"),
    ("lab", "Lab"),
    ("webinar", "Webinar"),
]

CERTIFICATE_TYPE_CHOICES = [
    ("completion", "Completion"),
    ("proficiency", "Proficiency"),
    ("specialist", "Specialist"),
    ("architect", "Architect"),
    ("partner", "Partner"),
]


class Course(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_course"

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    product_area = models.CharField(max_length=20, choices=PRODUCT_AREA_CHOICES)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES)
    level = models.CharField(max_length=20, choices=COURSE_LEVEL_CHOICES)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1)
    language_code = models.CharField(max_length=10, default="en")
    is_published = models.BooleanField(default=False)
    prerequisite_codes = models.JSONField(default=list)

    def __str__(self):
        return f"{self.title} ({self.code})"


class CourseModule(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_module"
        ordering = ["module_order"]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    module_order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_url = models.URLField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.code} — Module {self.module_order}: {self.title}"


class Enrollment(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_enrollment"

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    learner_id = models.UUIDField(db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_module_id = models.UUIDField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)

    def __str__(self):
        return f"Enrollment: {self.learner_id} in {self.course.code}"


class Exam(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_exam"

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    exam_title = models.CharField(max_length=200)
    pass_score_pct = models.PositiveIntegerField(default=70)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    question_bank = models.JSONField(default=list)
    is_proctored = models.BooleanField(default=False)
    attempts_allowed = models.PositiveIntegerField(default=3)

    def __str__(self):
        return f"{self.exam_title} — {self.course.code}"


class ExamAttempt(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_exam_attempt"

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    learner_id = models.UUIDField(db_index=True)
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    answers = models.JSONField(default=dict)

    def __str__(self):
        return f"Attempt {self.attempt_number} by {self.learner_id} on {self.exam.exam_title}"


class Certificate(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_certificate"

    learner_id = models.UUIDField(db_index=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    exam_attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPE_CHOICES)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, unique=True)
    verification_url = models.URLField(blank=True)
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Certificate {self.certificate_number} — {self.learner_id}"


class LearningPath(BaseModel):
    class Meta:
        app_label = "cybercom_academy"
        db_table = "cybercom_acad_learning_path"

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    target_role = models.CharField(max_length=100, blank=True)
    courses = models.ManyToManyField(Course, related_name="learning_paths", blank=True)
    estimated_weeks = models.PositiveIntegerField(null=True, blank=True)
    badge_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
