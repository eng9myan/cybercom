"""
Serializers for the assessment engine.

There are deliberately TWO families of quiz serializers:

  * the ``…Serializer`` family — authoring/marking view, includes the answer key
    (``Choice.is_correct`` and ``Question.accepted_answers``);
  * the ``Student…Serializer`` family — everything a learner is allowed to see,
    with the answer key structurally absent (not merely read-only).

views.py picks the family from the caller's role. Leaking the key is the obvious
failure mode of a quiz engine, so it is prevented by the shape of the payload
rather than by a filter someone can forget.
"""

from rest_framework import serializers

from products.cyed.assessment.models import (
    CHOICE_KINDS,
    KIND_SHORT_ANSWER,
    Answer,
    Assignment,
    Choice,
    Question,
    Quiz,
    QuizAttempt,
    Submission,
)

AUDIT_FIELDS = ["id", "tenant_id", "created_at", "updated_at"]


def _tenant_of(serializer):
    request = serializer.context.get("request")
    return getattr(request, "tenant_id", None)


def _incoming(serializer, attrs, field, default=None):
    """Value being written, falling back to the instance on a PATCH."""
    if field in attrs:
        return attrs[field]
    if serializer.instance is not None:
        return getattr(serializer.instance, field, default)
    return default


# ── Assignments & submissions ────────────────────────────────────────────────
class AssignmentSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, default="")
    is_overdue = serializers.BooleanField(read_only=True)
    max_score = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = "__all__"
        read_only_fields = list(AUDIT_FIELDS)

    def get_submission_count(self, obj) -> int:
        return obj.submissions.count()

    def validate_max_score(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("max_score must be greater than zero.")
        return value

    def validate(self, attrs):
        section = _incoming(self, attrs, "class_section")
        assessment = _incoming(self, attrs, "assessment")
        # A gradebook link that points at a different class is a data-integrity
        # trap: the Grade would land against the wrong cohort.
        if (
            assessment is not None
            and section is not None
            and assessment.class_section_id != section.id
        ):
            raise serializers.ValidationError(
                {"assessment": "The linked gradebook assessment belongs to a different class section."}
            )
        return attrs


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Full submission record. `score`/`feedback` are read-only on purpose — marks
    may only be written through the `grade` action so the gradebook write-back
    can never be bypassed.
    """

    student_name = serializers.SerializerMethodField()
    assignment_title = serializers.CharField(source="assignment.title", read_only=True, default="")
    percentage = serializers.FloatField(read_only=True)
    score = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    has_file = serializers.BooleanField(read_only=True)
    is_handed_in = serializers.BooleanField(read_only=True)

    class Meta:
        model = Submission
        exclude = ["file_bytes"]
        read_only_fields = AUDIT_FIELDS + [
            "submitted_at",
            "score",
            "feedback",
            "graded_by",
            "graded_at",
            "file_name",
            "content_type",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def validate(self, attrs):
        assignment = _incoming(self, attrs, "assignment")
        student = _incoming(self, attrs, "student")
        attempt_number = _incoming(self, attrs, "attempt_number") or 1
        status = _incoming(self, attrs, "status") or Submission.DRAFT

        # (tenant_id, assignment, student, attempt_number) is unique but
        # tenant_id is injected on save, so DRF cannot validate it — enforce it
        # here for a clean 400 instead of a 500 IntegrityError.
        if assignment is not None and student is not None:
            qs = Submission.objects.filter(
                tenant_id=_tenant_of(self),
                assignment=assignment,
                student=student,
                attempt_number=attempt_number,
            )
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "This student already has a submission for this assignment and attempt number. "
                    "Increment attempt_number to resubmit."
                )

        if status not in dict(Submission.STATUS):
            raise serializers.ValidationError({"status": "Unknown submission status."})

        # Handing in past a hard deadline is refused here too, so POSTing
        # status="submitted" cannot sneak past the `submit` action's rule.
        if (
            assignment is not None
            and status in (Submission.SUBMITTED, Submission.LATE)
            and not assignment.accepts_submission_at()
        ):
            raise serializers.ValidationError(
                {"status": "The due date has passed and this assignment does not accept late submissions."}
            )
        return attrs


class SubmissionGradeSerializer(serializers.Serializer):
    """Payload for the teacher `grade` action."""

    score = serializers.DecimalField(max_digits=7, decimal_places=2)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_score(self, value):
        if value < 0:
            raise serializers.ValidationError("Score cannot be negative.")
        assignment = self.context.get("assignment")
        if assignment is not None and value > assignment.max_score:
            raise serializers.ValidationError(
                f"Score cannot exceed the assignment maximum of {assignment.max_score}."
            )
        return value


# ── Quiz authoring (STAFF — carries the answer key) ──────────────────────────
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = "__all__"
        read_only_fields = list(AUDIT_FIELDS)


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    points = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)

    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = list(AUDIT_FIELDS)

    def validate_points(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("points cannot be negative.")
        return value

    def validate(self, attrs):
        kind = _incoming(self, attrs, "kind")
        accepted = _incoming(self, attrs, "accepted_answers")
        if accepted is not None and not isinstance(accepted, list):
            raise serializers.ValidationError(
                {"accepted_answers": "Must be a list of acceptable answer strings."}
            )
        if kind == KIND_SHORT_ANSWER and not (accepted or []):
            raise serializers.ValidationError(
                {"accepted_answers": "A short-answer question needs at least one accepted answer."}
            )
        if kind is not None and kind not in CHOICE_KINDS and kind != KIND_SHORT_ANSWER and accepted:
            raise serializers.ValidationError(
                {"accepted_answers": "Only short-answer questions use accepted_answers."}
            )
        return attrs


class QuizSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    question_count = serializers.SerializerMethodField()
    total_points = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)

    class Meta:
        model = Quiz
        fields = "__all__"
        read_only_fields = list(AUDIT_FIELDS)

    def get_question_count(self, obj) -> int:
        return obj.questions.count()

    def validate_max_attempts(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("max_attempts must be at least 1.")
        return value

    def validate_time_limit_minutes(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("time_limit_minutes must be at least 1 minute.")
        return value


class QuizDetailSerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True)


# ── Quiz sitting (STUDENT — answer key structurally absent) ──────────────────
class StudentChoiceSerializer(serializers.ModelSerializer):
    """Note the field list: `is_correct` is not present at all."""

    class Meta:
        model = Choice
        fields = ["id", "question", "text", "sequence"]


class StudentQuestionSerializer(serializers.ModelSerializer):
    """Note the field list: `accepted_answers` (the short-answer key) is absent."""

    choices = StudentChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "kind", "points", "sequence", "choices"]


class StudentQuizSerializer(serializers.ModelSerializer):
    class_section_name = serializers.CharField(source="class_section.name", read_only=True, default="")
    question_count = serializers.SerializerMethodField()
    total_points = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "class_section",
            "class_section_name",
            "lesson",
            "title",
            "description",
            "time_limit_minutes",
            "max_attempts",
            "shuffle_questions",
            "curriculum_code",
            "is_published",
            "question_count",
            "total_points",
            "created_at",
        ]

    def get_question_count(self, obj) -> int:
        return obj.questions.count()


class StudentQuizDetailSerializer(StudentQuizSerializer):
    questions = StudentQuestionSerializer(many=True, read_only=True)

    class Meta(StudentQuizSerializer.Meta):
        fields = StudentQuizSerializer.Meta.fields + ["questions"]


# ── Attempts & answers ───────────────────────────────────────────────────────
class AnswerSerializer(serializers.ModelSerializer):
    awarded_points = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    question_kind = serializers.CharField(source="question.kind", read_only=True, default="")

    class Meta:
        model = Answer
        fields = "__all__"
        read_only_fields = AUDIT_FIELDS + ["awarded_points", "is_correct"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    quiz_title = serializers.CharField(source="quiz.title", read_only=True, default="")
    percentage = serializers.FloatField(read_only=True)
    score = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    max_score = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = "__all__"
        read_only_fields = AUDIT_FIELDS + ["score", "max_score", "is_graded", "submitted_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def validate(self, attrs):
        quiz = _incoming(self, attrs, "quiz")
        student = _incoming(self, attrs, "student")
        attempt_number = _incoming(self, attrs, "attempt_number") or 1
        if quiz is not None and student is not None:
            qs = QuizAttempt.objects.filter(
                tenant_id=_tenant_of(self),
                quiz=quiz,
                student=student,
                attempt_number=attempt_number,
            )
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "That attempt number already exists for this student and quiz."
                )
            if self.instance is None:
                used = QuizAttempt.objects.filter(
                    tenant_id=_tenant_of(self), quiz=quiz, student=student
                ).count()
                if quiz.max_attempts and used >= quiz.max_attempts:
                    raise serializers.ValidationError(
                        f"This quiz allows at most {quiz.max_attempts} attempt(s) per student."
                    )
        return attrs


class MarkAnswerSerializer(serializers.Serializer):
    """Payload for a teacher marking an extended-response answer."""

    answer = serializers.UUIDField()
    awarded_points = serializers.DecimalField(max_digits=6, decimal_places=2)
    is_correct = serializers.BooleanField(required=False, allow_null=True, default=None)
