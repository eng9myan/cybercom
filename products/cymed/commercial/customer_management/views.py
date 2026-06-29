from products.cymed.commercial.customer_management.models import (
    Customer,
    CustomerContract,
    CustomerDeployment,
    CustomerOrganization,
    CustomerSuccessPlan,
)
from products.cymed.commercial.customer_management.serializers import (
    CustomerContractSerializer,
    CustomerDeploymentSerializer,
    CustomerOrganizationSerializer,
    CustomerSerializer,
    CustomerSuccessPlanSerializer,
)
from products.cymed.commercial.views import CommercialModelViewSet


class CustomerViewSet(CommercialModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerOrganizationViewSet(CommercialModelViewSet):
    queryset = CustomerOrganization.objects.all()
    serializer_class = CustomerOrganizationSerializer


class CustomerContractViewSet(CommercialModelViewSet):
    queryset = CustomerContract.objects.all()
    serializer_class = CustomerContractSerializer


class CustomerDeploymentViewSet(CommercialModelViewSet):
    queryset = CustomerDeployment.objects.all()
    serializer_class = CustomerDeploymentSerializer


class CustomerSuccessPlanViewSet(CommercialModelViewSet):
    queryset = CustomerSuccessPlan.objects.all()
    serializer_class = CustomerSuccessPlanSerializer
