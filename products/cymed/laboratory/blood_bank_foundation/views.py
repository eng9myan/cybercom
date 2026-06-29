from ..views import LaboratoryModelViewSet
from .models import BloodCompatibility, BloodInventory, BloodProduct, TransfusionRequest
from .serializers import (
    BloodCompatibilitySerializer,
    BloodInventorySerializer,
    BloodProductSerializer,
    TransfusionRequestSerializer,
)


class BloodProductViewSet(LaboratoryModelViewSet):
    queryset = BloodProduct.objects.all()
    serializer_class = BloodProductSerializer
    required_feature = "lab.blood_bank"
    filterset_fields = ["product_type", "blood_group", "rh_type", "status"]
    search_fields = ["unit_number"]


class BloodInventoryViewSet(LaboratoryModelViewSet):
    queryset = BloodInventory.objects.all()
    serializer_class = BloodInventorySerializer
    required_feature = "lab.blood_bank"
    filterset_fields = ["product_type", "blood_group", "rh_type"]


class BloodCompatibilityViewSet(LaboratoryModelViewSet):
    queryset = BloodCompatibility.objects.all()
    serializer_class = BloodCompatibilitySerializer
    required_feature = "lab.blood_bank"
    filterset_fields = ["patient_id", "blood_group", "antibody_screen"]


class TransfusionRequestViewSet(LaboratoryModelViewSet):
    queryset = TransfusionRequest.objects.all()
    serializer_class = TransfusionRequestSerializer
    required_feature = "lab.blood_bank"
    filterset_fields = ["patient_id", "status", "urgency", "product_type"]
