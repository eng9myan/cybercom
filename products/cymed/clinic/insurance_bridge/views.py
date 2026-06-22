from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.insurance_bridge.models import Payer, InsurancePlan, EligibilityCheck, AuthorizationRequest, AuthorizationResponse
from products.cymed.clinic.insurance_bridge.serializers import (
    PayerSerializer, InsurancePlanSerializer, EligibilityCheckSerializer,
    AuthorizationRequestSerializer, AuthorizationResponseSerializer
)

class PayerViewSet(ClinicModelViewSet):
    queryset = Payer.objects.all()
    serializer_class = PayerSerializer

class InsurancePlanViewSet(ClinicModelViewSet):
    queryset = InsurancePlan.objects.all()
    serializer_class = InsurancePlanSerializer

class EligibilityCheckViewSet(ClinicModelViewSet):
    queryset = EligibilityCheck.objects.all()
    serializer_class = EligibilityCheckSerializer

class AuthorizationRequestViewSet(ClinicModelViewSet):
    queryset = AuthorizationRequest.objects.all()
    serializer_class = AuthorizationRequestSerializer

class AuthorizationResponseViewSet(ClinicModelViewSet):
    queryset = AuthorizationResponse.objects.all()
    serializer_class = AuthorizationResponseSerializer

