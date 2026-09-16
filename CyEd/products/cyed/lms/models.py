from django.db import models

from platform.common.models import BaseModel
from products.cyed.sis.models import ClassSection


class Course(BaseModel):
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(default=7)
    class_section = models.ForeignKey(
        ClassSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_lms_courses"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Module(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    name = models.CharField(max_length=255)
    sequence = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cyed_lms_modules"
        ordering = ["sequence", "name"]

    def __str__(self):
        return f"{self.course_id} · {self.name}"


class Lesson(BaseModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    # ACARA content-description code this lesson addresses (e.g. AC9M8N01).
    curriculum_code = models.CharField(max_length=50, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)
    estimated_minutes = models.PositiveSmallIntegerField(default=45)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_lms_lessons"
        ordering = ["sequence", "title"]

    def __str__(self):
        return self.title
