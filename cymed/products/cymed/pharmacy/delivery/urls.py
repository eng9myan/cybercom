"""CyMed Pharmacy Delivery URL routes."""
from django.urls import path

from .views import (
    CourierViewSet,
    DeliveryJobViewSet,
    DeliveryStatusEventViewSet,
    RiderViewSet,
)

courier_list = CourierViewSet.as_view({"get": "list", "post": "create"})
courier_detail = CourierViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

rider_list = RiderViewSet.as_view({"get": "list", "post": "create"})
rider_detail = RiderViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

job_list = DeliveryJobViewSet.as_view({"get": "list", "post": "create"})
job_detail = DeliveryJobViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
job_create_job = DeliveryJobViewSet.as_view({"post": "create_job"})
job_assign_rider = DeliveryJobViewSet.as_view({"post": "assign_rider"})
job_update_status = DeliveryJobViewSet.as_view({"post": "update_status"})
job_upload_proof = DeliveryJobViewSet.as_view({"post": "upload_proof"})
job_dispatch = DeliveryJobViewSet.as_view({"post": "dispatch_action"})
job_kpi = DeliveryJobViewSet.as_view({"get": "kpi_snapshot"})

event_list = DeliveryStatusEventViewSet.as_view({"get": "list"})
event_detail = DeliveryStatusEventViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("couriers/", courier_list, name="cymed-delivery-courier-list"),
    path("couriers/<uuid:pk>/", courier_detail, name="cymed-delivery-courier-detail"),
    path("riders/", rider_list, name="cymed-delivery-rider-list"),
    path("riders/<uuid:pk>/", rider_detail, name="cymed-delivery-rider-detail"),
    path("jobs/", job_list, name="cymed-delivery-job-list"),
    path("jobs/<uuid:pk>/", job_detail, name="cymed-delivery-job-detail"),
    path("jobs/create-job/", job_create_job, name="cymed-delivery-job-create-job"),
    path("jobs/<uuid:pk>/assign-rider/", job_assign_rider, name="cymed-delivery-job-assign-rider"),
    path("jobs/<uuid:pk>/update-status/", job_update_status, name="cymed-delivery-job-update-status"),
    path("jobs/<uuid:pk>/upload-proof/", job_upload_proof, name="cymed-delivery-job-upload-proof"),
    path("jobs/<uuid:pk>/dispatch/", job_dispatch, name="cymed-delivery-job-dispatch"),
    path("jobs/kpi-snapshot/", job_kpi, name="cymed-delivery-job-kpi-snapshot"),
    path("events/", event_list, name="cymed-delivery-event-list"),
    path("events/<uuid:pk>/", event_detail, name="cymed-delivery-event-detail"),
]
