from products.cymed.commercial.partner_management.models import (
    DistributorAgreement,
    Partner,
    PartnerType,
    ResellerAgreement,
)
from products.cymed.commercial.partner_management.serializers import (
    DistributorAgreementSerializer,
    PartnerSerializer,
    PartnerTypeSerializer,
    ResellerAgreementSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class PartnerTypeViewSet(CommercialModelViewSet):
    queryset = PartnerType.objects.all()
    serializer_class = PartnerTypeSerializer


class PartnerViewSet(CommercialModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer


class ResellerAgreementViewSet(CommercialModelViewSet):
    queryset = ResellerAgreement.objects.all()
    serializer_class = ResellerAgreementSerializer


class DistributorAgreementViewSet(CommercialModelViewSet):
    queryset = DistributorAgreement.objects.all()
    serializer_class = DistributorAgreementSerializer
