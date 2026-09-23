from django.urls import path

from products.cycom.cms import views

urlpatterns = [
    path("<slug:slug>/", views.public_homepage, name="cms-public-homepage"),
    path("<slug:slug>/pages/<slug:page_slug>/", views.public_page_detail, name="cms-public-page-detail"),
]
