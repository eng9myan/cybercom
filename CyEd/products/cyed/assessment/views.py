"""
API surface for the assessment engine.

RBAC summary (each boundary has a test in test_assessment.py):
  * staff (admin/leadership/teacher/pastoral/finance) author, publish and mark;
  * students see only PUBLISHED work for class sections they are enrolled in,
    and only their OWN submissions/attempts/answers;
  * students never receive `Choice.is_correct` or `Question.accepted_answers`
    before submitting — the student serializers simply do not contain them;
  * parents get read-only access to their own children's work;
  * only staff may publish.
"""

import random

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.assessment import services
from products.cyed.assessment.models import (
    Answer,
    Assignment,
    Choice,
    Question,
    Quiz,
    QuizAttempt,
    Submission,
)
from products.cyed.assessment.serializers import (
    AnswerSerializer,
    AssignmentSerializer,
    ChoiceSerializer,
    MarkAnswerSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizDetailSerializer,
    QuizSerializer,
    StudentChoiceSerializer,
    StudentQuestionSerializer,
    StudentQuizDetailSerializer,
    StudentQuizSerializer,
    SubmissionGradeSerializer,
    SubmissionSerializer,
)
from products.cyed.governance.access import (
    PARENT,
    STUDENT,
    IsStaff,
    _email,
    has_any,
    is_staff,
    scope_queryset_by_student,
    visible_student_ids,
)


# ── Permissions ──────────────────────────────────────────────────────────────
class StaffWritesOnly(BasePermission):
    """Anyone authenticated may read (the queryset does the narrowing); only
    staff may create/update/delete — this is what makes publishing staff-only."""

    def has_permission(self, request, view) -> bool:
        if getattr(request, "auth_claims", None) is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_staff(request)


class StaffOrStudentWrites(BasePermission):
    """Staff or a student may write (a student only for themselves — enforced in
    the viewset). Parents are read-only everywhere in this app."""

    def has_permission(self, request, view) -> bool:
        if getattr(request, "auth_claims", None) is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_staff(request) or has_any(request, STUDENT)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _own_student(request):
    """The Student row belonging to the caller (matched on email), or None."""
    from products.cyed.sis.models import Student

    if not has_any(request, STUDENT):
        return None
    email = _email(request)
    if not email:
        return None
    return Student.objects.filter(tenant_id=request.tenant_id, email__iexact=email).first()


def _sections_for_students(tenant_id, student_ids):
    from products.cyed.sis.models import Enrolment

    return set(
        Enrolment.objects.filter(
            tenant_id=tenant_id, student_id__in=list(student_ids), status="active"
        ).values_list("class_section_id", flat=True)
    )


def _visible_section_ids(request):
    """Class sections whose work this caller may see; None means "all" (staff)."""
    student_ids = visible_student_ids(request, request.tenant_id)
    if student_ids is None:
        return None
    if not student_ids:
        return set()
    return _sections_for_students(request.tenant_id, student_ids)


def _refused(exc) -> Response:
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


def _forbidden(detail) -> Response:
    return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)


def _maybe_shuffle(quiz, data, request):
    """Randomise question order for learners when the quiz asks for it."""
    if quiz.shuffle_questions and not is_staff(request) and data.get("questions"):
        questions = list(data["questions"])
        random.shuffle(questions)
        data["questions"] = questions
    return data


# ── Assignments ──────────────────────────────────────────────────────────────
class AssignmentViewSet(TenantScopedModelViewSet):
    """Teachers author assignments; learners and their parents read published ones."""

    queryset = Assignment.objects.select_related("class_section", "lesson", "assessment").all()
    serializer_class = AssignmentSerializer
    permission_classes = [StaffWritesOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        sections = _visible_section_ids(self.request)
        if sections is not None:
            # Non-staff: published work for their own class sections only.
            qs = qs.filter(is_published=True, class_section_id__in=sections)
        params = self.request.query_params
        if params.get("class_section"):
            qs = qs.filter(class_section_id=params["class_section"])
        if params.get("lesson"):
            qs = qs.filter(lesson_id=params["lesson"])
        if params.get("curriculum_code"):
            qs = qs.filter(curriculum_code=params["curriculum_code"])
        if params.get("is_published") in ("true", "false"):
            qs = qs.filter(is_published=params["is_published"] == "true")
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def publish(self, request, pk=None):
        assignment = self.get_object()
        assignment.is_published = True
        assignment.save(update_fields=["is_published", "updated_at"])
        return Response(self.get_serializer(assignment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def unpublish(self, request, pk=None):
        assignment = self.get_object()
        assignment.is_published = False
        assignment.save(update_fields=["is_published", "updated_at"])
        return Response(self.get_serializer(assignment).data)

    @action(detail=True, methods=["get"], permission_classes=[IsStaff])
    def submissions(self, request, pk=None):
        """Marking view: every submission for this assignment (staff only)."""
        assignment = self.get_object()
        rows = (
            Submission.objects.filter(tenant_id=request.tenant_id, assignment=assignment)
            .select_related("student", "assignment")
            .order_by("student__last_name", "attempt_number")
        )
        data = SubmissionSerializer(rows, many=True, context=self.get_serializer_context()).data
        handed_in = [r for r in rows if r.is_handed_in]
        return Response(
            {
                "assignment": str(assignment.id),
                "title": assignment.title,
                "count": len(data),
                "handed_in": len(handed_in),
                "graded": len([r for r in rows if r.status == Submission.GRADED]),
                "late": len([r for r in rows if r.status == Submission.LATE]),
                "results": data,
            }
        )

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """
        "My assignments": every published assignment for the learner's classes,
        each tagged submitted / outstanding. Parents get the same view for each
        of their children; staff must name a student explicitly.
        """
        student_ids = visible_student_ids(request, request.tenant_id)
        if student_ids is None:  # staff
            requested = request.query_params.get("student")
            if not requested:
                return Response(
                    {"detail": "Staff must pass ?student=<uuid> — use /assignments/{id}/submissions/ for a class view."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            student_ids = {requested}

        rows = []
        for student_id in student_ids:
            sections = _sections_for_students(request.tenant_id, [student_id])
            assignments = Assignment.objects.filter(
                tenant_id=request.tenant_id, is_published=True, class_section_id__in=sections
            ).order_by("due_at", "-created_at")
            submissions = {
                s.assignment_id: s
                for s in Submission.objects.filter(
                    tenant_id=request.tenant_id, student_id=student_id, assignment__in=assignments
                ).order_by("attempt_number")
            }
            for assignment in assignments:
                sub = submissions.get(assignment.id)
                rows.append(
                    {
                        "student": str(student_id),
                        "assignment": str(assignment.id),
                        "title": assignment.title,
                        "class_section": str(assignment.class_section_id),
                        "due_at": assignment.due_at,
                        "is_overdue": assignment.is_overdue,
                        "allow_late": assignment.allow_late,
                        "max_score": str(assignment.max_score),
                        "curriculum_code": assignment.curriculum_code,
                        "status": sub.status if sub else "outstanding",
                        "submission": str(sub.id) if sub else None,
                        "submitted_at": sub.submitted_at if sub else None,
                        "score": str(sub.score) if sub and sub.score is not None else None,
                    }
                )
        return Response(
            {
                "count": len(rows),
                "outstanding": len([r for r in rows if r["status"] == "outstanding"]),
                "results": rows,
            }
        )


class SubmissionViewSet(TenantScopedModelViewSet):
    """
    A learner's work. Students see and write only their own; parents read their
    children's; staff see the lot and are the only ones who may mark.
    """

    queryset = Submission.objects.select_related("assignment", "student").all()
    serializer_class = SubmissionSerializer
    permission_classes = [StaffOrStudentWrites]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(
            self.request, self.request.tenant_id, qs, student_path="student_id"
        )
        params = self.request.query_params
        if params.get("assignment"):
            qs = qs.filter(assignment_id=params["assignment"])
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def _own_student_guard(self, serializer):
        """A student may only file work under their own name."""
        if is_staff(self.request):
            return None
        me = _own_student(self.request)
        target = serializer.validated_data.get("student") or getattr(
            serializer.instance, "student", None
        )
        if me is None or target is None or str(target.id) != str(me.id):
            return _forbidden("You may only create or change your own submissions.")
        return None

    def _attach_file(self, instance):
        upload = self.request.FILES.get("file")
        if upload is None:
            return
        instance.file_bytes = upload.read()
        instance.file_name = getattr(upload, "name", "") or ""
        instance.content_type = getattr(upload, "content_type", "") or ""
        instance.save(update_fields=["file_bytes", "file_name", "content_type", "updated_at"])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        denied = self._own_student_guard(serializer)
        if denied is not None:
            return denied
        instance = serializer.save(tenant_id=request.tenant_id)
        self._attach_file(instance)
        if instance.status in (Submission.SUBMITTED, Submission.LATE):
            try:
                services.submit_submission(instance)
            except services.AssessmentRefused as exc:  # pragma: no cover - serializer catches first
                instance.delete()
                return _refused(exc)
        return Response(
            self.get_serializer(instance).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if not is_staff(request) and instance.status in Submission.HANDED_IN:
            return _forbidden("A submission that has been handed in can no longer be edited.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        denied = self._own_student_guard(serializer)
        if denied is not None:
            return denied
        instance = serializer.save()
        self._attach_file(instance)
        return Response(self.get_serializer(instance).data)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        Hand in. Past the deadline: refused when allow_late is False, accepted
        and flagged `late` when it is True.
        """
        submission = self.get_object()
        if not is_staff(request):
            me = _own_student(request)
            if me is None or str(me.id) != str(submission.student_id):
                return _forbidden("You may only submit your own work.")
        if submission.status in (Submission.GRADED, Submission.RETURNED):
            return Response(
                {"detail": "This submission has already been marked."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        text = request.data.get("text_response")
        if text is not None:
            submission.text_response = text
            submission.save(update_fields=["text_response", "updated_at"])
        self._attach_file(submission)
        try:
            services.submit_submission(submission)
        except services.AssessmentRefused as exc:
            return _refused(exc)
        return Response(self.get_serializer(submission).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def grade(self, request, pk=None):
        """
        Mark a submission. When the assignment is linked to a
        gradebook.Assessment this also writes the gradebook.Grade — that link is
        the entire reason this app exists.
        """
        submission = self.get_object()
        payload = SubmissionGradeSerializer(
            data=request.data, context={"assignment": submission.assignment}
        )
        payload.is_valid(raise_exception=True)
        submission, grade = services.grade_submission(
            submission,
            score=payload.validated_data["score"],
            feedback=payload.validated_data.get("feedback", ""),
            marker=_email(request),
        )
        data = self.get_serializer(submission).data
        data["gradebook_grade"] = str(grade.id) if grade else None
        return Response(data)

    @action(detail=True, methods=["post"], url_path="return", permission_classes=[IsStaff])
    def return_to_student(self, request, pk=None):
        submission = self.get_object()
        if submission.score is None:
            return Response(
                {"detail": "Mark the submission before returning it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.status = Submission.RETURNED
        submission.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(submission).data)

    @action(detail=True, methods=["get"])
    def file(self, request, pk=None):
        """Download the uploaded attachment (queryset scoping is the guard)."""
        submission = self.get_object()
        if not submission.file_bytes:
            return Response(
                {"detail": "No file attached to this submission."},
                status=status.HTTP_404_NOT_FOUND,
            )
        response = HttpResponse(
            bytes(submission.file_bytes),
            content_type=submission.content_type or "application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{submission.file_name or "submission"}"'
        )
        return response


# ── Quizzes ──────────────────────────────────────────────────────────────────
class QuizViewSet(TenantScopedModelViewSet):
    queryset = Quiz.objects.select_related("class_section", "lesson").prefetch_related(
        "questions__choices"
    )
    serializer_class = QuizSerializer
    permission_classes = [StaffWritesOnly]

    def get_serializer_class(self):
        staff = is_staff(self.request)
        if self.action == "retrieve":
            return QuizDetailSerializer if staff else StudentQuizDetailSerializer
        return QuizSerializer if staff else StudentQuizSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        sections = _visible_section_ids(self.request)
        if sections is not None:
            qs = qs.filter(is_published=True, class_section_id__in=sections)
        params = self.request.query_params
        if params.get("class_section"):
            qs = qs.filter(class_section_id=params["class_section"])
        if params.get("lesson"):
            qs = qs.filter(lesson_id=params["lesson"])
        return qs

    def retrieve(self, request, *args, **kwargs):
        quiz = self.get_object()
        return Response(_maybe_shuffle(quiz, self.get_serializer(quiz).data, request))

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def publish(self, request, pk=None):
        quiz = self.get_object()
        if not quiz.questions.exists():
            return Response(
                {"detail": "Add at least one question before publishing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        quiz.is_published = True
        quiz.save(update_fields=["is_published", "updated_at"])
        return Response(QuizSerializer(quiz, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedViaClaims])
    def start(self, request, pk=None):
        """
        Open an attempt. Students start their own; staff may start one on a
        named student's behalf. Quiz.max_attempts is enforced here.

        The viewset is otherwise staff-write, so this action opts back in to
        plain authentication — sitting a quiz is the one write a learner makes.
        """
        quiz = self.get_object()  # unpublished quizzes are already invisible to students
        if is_staff(request):
            student_id = request.data.get("student")
            if not student_id:
                return Response(
                    {"detail": "Pass `student` to start an attempt on a learner's behalf."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            from products.cyed.sis.models import Student

            student = Student.objects.filter(
                tenant_id=request.tenant_id, id=student_id
            ).first()
            if student is None:
                return Response(
                    {"detail": "Unknown student."}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            student = _own_student(request)
            if student is None:
                return _forbidden(
                    "No student record is linked to your account, so you cannot sit this quiz."
                )

        try:
            attempt = services.start_attempt(quiz, student, request.tenant_id)
        except services.AssessmentRefused as exc:
            return _refused(exc)

        context = self.get_serializer_context()
        quiz_payload = (
            QuizDetailSerializer(quiz, context=context)
            if is_staff(request)
            else StudentQuizDetailSerializer(quiz, context=context)
        ).data
        return Response(
            {
                "attempt": QuizAttemptSerializer(attempt, context=context).data,
                "quiz": _maybe_shuffle(quiz, quiz_payload, request),
            },
            status=status.HTTP_201_CREATED,
        )


class QuestionViewSet(TenantScopedModelViewSet):
    """
    Authoring endpoint. Students may read questions of published quizzes for
    their own classes — through a serializer that has no answer-key fields.
    """

    queryset = Question.objects.select_related("quiz").prefetch_related("choices")
    serializer_class = QuestionSerializer
    permission_classes = [StaffWritesOnly]

    def get_serializer_class(self):
        return QuestionSerializer if is_staff(self.request) else StudentQuestionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        sections = _visible_section_ids(self.request)
        if sections is not None:
            qs = qs.filter(quiz__is_published=True, quiz__class_section_id__in=sections)
        if self.request.query_params.get("quiz"):
            qs = qs.filter(quiz_id=self.request.query_params["quiz"])
        return qs


class ChoiceViewSet(TenantScopedModelViewSet):
    """
    Options for a question. `is_correct` is the answer key: it is present only
    in the staff serializer, so a learner physically cannot read it here.
    """

    queryset = Choice.objects.select_related("question", "question__quiz").all()
    serializer_class = ChoiceSerializer
    permission_classes = [StaffWritesOnly]

    def get_serializer_class(self):
        return ChoiceSerializer if is_staff(self.request) else StudentChoiceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        sections = _visible_section_ids(self.request)
        if sections is not None:
            qs = qs.filter(
                question__quiz__is_published=True,
                question__quiz__class_section_id__in=sections,
            )
        if self.request.query_params.get("question"):
            qs = qs.filter(question_id=self.request.query_params["question"])
        return qs


class QuizAttemptViewSet(TenantScopedModelViewSet):
    """
    A sitting of a quiz. Students reach their own attempts only (parents their
    children's); attempts are opened via /quizzes/{id}/start/, so direct writes
    here are staff-only.
    """

    queryset = QuizAttempt.objects.select_related("quiz", "student").all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [StaffWritesOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(
            self.request, self.request.tenant_id, qs, student_path="student_id"
        )
        params = self.request.query_params
        if params.get("quiz"):
            qs = qs.filter(quiz_id=params["quiz"])
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        return qs

    def _may_act_on(self, request, attempt) -> bool:
        if is_staff(request):
            return True
        me = _own_student(request)
        return me is not None and str(me.id) == str(attempt.student_id)

    @action(
        detail=True, methods=["post"], url_path="answer", permission_classes=[IsAuthenticatedViaClaims]
    )
    def answer(self, request, pk=None):
        """Save one answer mid-attempt. Nothing is marked or revealed yet."""
        attempt = self.get_object()
        if not self._may_act_on(request, attempt):
            return _forbidden("You may only answer your own attempt.")
        if attempt.submitted_at is not None:
            return Response(
                {"detail": "This attempt has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        question = attempt.quiz.questions.filter(id=request.data.get("question")).first()
        if question is None:
            return Response(
                {"detail": "That question does not belong to this quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        answer = services.save_answer(
            attempt,
            question,
            selected_choice_ids=request.data.get("choices") or [],
            text_answer=request.data.get("text_answer", ""),
        )
        return Response(
            AnswerSerializer(answer, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedViaClaims])
    def submit(self, request, pk=None):
        """
        Hand the quiz in and auto-mark it. Accepts the whole answer set in one
        call: {"answers": [{"question": id, "choices": [id...], "text_answer": ""}]}
        """
        attempt = self.get_object()
        if not self._may_act_on(request, attempt):
            return _forbidden("You may only submit your own attempt.")
        try:
            result = services.submit_attempt(attempt, request.data.get("answers") or [])
        except services.AssessmentRefused as exc:
            return _refused(exc)
        return Response(result)

    @action(detail=True, methods=["get"])
    def review(self, request, pk=None):
        """
        Post-submission review — the ONLY place a learner ever sees the answer
        key, and only for their own, already-submitted attempt.
        """
        attempt = self.get_object()
        if not self._may_act_on(request, attempt) and not has_any(request, PARENT):
            return _forbidden("You may only review your own attempt.")
        if attempt.submitted_at is None and not is_staff(request):
            return Response(
                {"detail": "Submit the attempt before reviewing it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reveal = attempt.submitted_at is not None
        return Response(services.grade_attempt(attempt, reveal_key=reveal))

    @action(detail=True, methods=["post"], url_path="mark-answer", permission_classes=[IsStaff])
    def mark_answer(self, request, pk=None):
        """Human marking of an extended response; re-rolls the attempt total."""
        attempt = self.get_object()
        payload = MarkAnswerSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        answer = attempt.answers.filter(id=payload.validated_data["answer"]).first()
        if answer is None:
            return Response(
                {"detail": "That answer does not belong to this attempt."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        services.mark_answer(
            answer,
            payload.validated_data["awarded_points"],
            payload.validated_data.get("is_correct"),
        )
        return Response(services.grade_attempt(attempt, reveal_key=True))


class AnswerViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Read-only: answers are written through the attempt actions so they can never
    be edited after marking. Scoped to the caller's own (or their children's)
    attempts.
    """

    # Declared so the OpenAPI generator can infer the model; get_queryset below
    # is what actually runs, and it always narrows by tenant and student.
    queryset = Answer.objects.none()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticatedViaClaims]

    def get_queryset(self):
        qs = Answer.objects.select_related("attempt", "question").prefetch_related(
            "selected_choices"
        )
        # Mirrors TenantScopedModelViewSet: tenant_id is None only for a
        # platform_admin operating cross-tenant.
        if self.request.tenant_id is not None:
            qs = qs.filter(tenant_id=self.request.tenant_id)
        qs = scope_queryset_by_student(
            self.request, self.request.tenant_id, qs, student_path="attempt__student_id"
        )
        if self.request.query_params.get("attempt"):
            qs = qs.filter(attempt_id=self.request.query_params["attempt"])
        return qs
