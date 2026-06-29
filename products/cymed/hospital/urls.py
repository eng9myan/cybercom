from django.urls import include, path

urlpatterns = [
    path("adt/", include("products.cymed.hospital.adt.urls")),
    path("beds/", include("products.cymed.hospital.bed_management.urls")),
    path("emergency/", include("products.cymed.hospital.emergency.urls")),
    path("inpatient/", include("products.cymed.hospital.inpatient.urls")),
    path("nursing/", include("products.cymed.hospital.nursing.urls")),
    path("icu/", include("products.cymed.hospital.icu.urls")),
    path("or/", include("products.cymed.hospital.operating_room.urls")),
    path("anesthesia/", include("products.cymed.hospital.anesthesia.urls")),
    path("maternity/", include("products.cymed.hospital.maternity.urls")),
    path("transfer-center/", include("products.cymed.hospital.transfer_center.urls")),
    path("discharge/", include("products.cymed.hospital.discharge.urls")),
    path("command-center/", include("products.cymed.hospital.clinical_command_center.urls")),
    path("capacity/", include("products.cymed.hospital.capacity_management.urls")),
]
