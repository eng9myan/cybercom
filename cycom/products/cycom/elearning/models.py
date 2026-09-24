import secrets

from django.db import models

from platform.common.models import BaseModel
from platform.common.slugs import unique_slugify


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


class Course(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_elearning_courses"
        unique_together = [("tenant_id", "slug")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                Course.objects.filter(tenant_id=self.tenant_id), self.title, exclude_pk=self.pk
            )
        super().save(*args, **kwargs)


class Lesson(BaseModel):
    course = models.ForeignKey(Course, related_name="lessons", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cycom_elearning_lessons"
        unique_together = [("course", "slug")]
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                Lesson.objects.filter(course_id=self.course_id), self.title, exclude_pk=self.pk
            )
        super().save(*args, **kwargs)


class Enrollment(BaseModel):
    """A student's enrollment, reachable via an unguessable public token
    (same posture as esign/storefront/livechat) so progress can be tracked
    across visits without a real login."""

    course = models.ForeignKey(Course, related_name="enrollments", on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=_generate_token, editable=False)
    student_name = models.CharField(max_length=255, blank=True)
    student_email = models.EmailField(blank=True)

    class Meta:
        db_table = "cycom_elearning_enrollments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student_name or 'Guest'} -> {self.course_id}"


class LessonProgress(BaseModel):
    """One completed lesson for one enrollment. Existence of the row IS
    completion — `created_at` doubles as the completion timestamp."""

    enrollment = models.ForeignKey(Enrollment, related_name="progress", on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, related_name="+", on_delete=models.CASCADE)

    class Meta:
        db_table = "cycom_elearning_lesson_progress"
        unique_together = [("enrollment", "lesson")]
