from django.urls import path

from products.cycom.hitl import views

urlpatterns = [
    path("queue/", views.hitl_queue, name="hitl-queue"),
    path("approve/<uuid:item_id>/", views.hitl_approve, name="hitl-approve"),
    path("reject/<uuid:item_id>/", views.hitl_reject, name="hitl-reject"),
]
