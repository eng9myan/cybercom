from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.customer_management.models import (
    Customer, CustomerOrganization, CustomerContract,
    CustomerDeployment, CustomerSuccessPlan
)
from products.cymed.commercial.customer_management.serializers import (
    CustomerSerializer, CustomerOrganizationSerializer, CustomerContractSerializer,
    CustomerDeploymentSerializer, CustomerSuccessPlanSerializer
)


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
