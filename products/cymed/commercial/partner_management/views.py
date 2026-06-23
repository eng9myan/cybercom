from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.partner_management.models import (
    PartnerType, Partner, ResellerAgreement, DistributorAgreement
)
from products.cymed.commercial.partner_management.serializers import (
    PartnerTypeSerializer, PartnerSerializer,
    ResellerAgreementSerializer, DistributorAgreementSerializer
)


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
