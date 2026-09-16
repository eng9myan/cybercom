from rest_framework.routers import DefaultRouter

from products.cyed.assessment.views import (
    AnswerViewSet,
    AssignmentViewSet,
    ChoiceViewSet,
    QuestionViewSet,
    QuizAttemptViewSet,
    QuizViewSet,
    SubmissionViewSet,
)

router = DefaultRouter()
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", SubmissionViewSet, basename="submission")
router.register("quizzes", QuizViewSet, basename="quiz")
router.register("questions", QuestionViewSet, basename="question")
router.register("choices", ChoiceViewSet, basename="choice")
router.register("attempts", QuizAttemptViewSet, basename="quiz-attempt")
router.register("answers", AnswerViewSet, basename="quiz-answer")

urlpatterns = router.urls
