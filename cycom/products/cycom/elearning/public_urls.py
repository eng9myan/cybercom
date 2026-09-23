from django.urls import path

from products.cycom.elearning import views

urlpatterns = [
    path("<slug:slug>/courses/", views.public_course_list, name="elearning-public-courses"),
    path("<slug:slug>/courses/<slug:course_slug>/", views.public_course_detail, name="elearning-public-course-detail"),
    path("<slug:slug>/courses/<slug:course_slug>/enroll/", views.public_enroll, name="elearning-public-enroll"),
    path(
        "<slug:slug>/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/",
        views.public_lesson_detail,
        name="elearning-public-lesson-detail",
    ),
    path(
        "<slug:slug>/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/progress/",
        views.public_lesson_progress,
        name="elearning-public-lesson-progress",
    ),
]
