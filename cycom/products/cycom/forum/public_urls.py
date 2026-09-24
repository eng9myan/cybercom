from django.urls import path

from products.cycom.forum import views

urlpatterns = [
    path("<slug:slug>/threads/", views.public_thread_list, name="forum-public-threads"),
    path("<slug:slug>/threads/<slug:thread_slug>/", views.public_thread_detail, name="forum-public-thread-detail"),
    path(
        "<slug:slug>/threads/<slug:thread_slug>/replies/",
        views.public_reply_create,
        name="forum-public-reply-create",
    ),
]
