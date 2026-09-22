from django.urls import path

from products.cycom.blog import views

urlpatterns = [
    path("<slug:slug>/posts/", views.public_post_list, name="blog-public-posts"),
    path("<slug:slug>/posts/<slug:post_slug>/", views.public_post_detail, name="blog-public-post-detail"),
]
