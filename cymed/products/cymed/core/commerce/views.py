from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.wallet.services import InsufficientFundsError, resolve_person_from_request
from products.cymed.core.commerce.checkout import (
    CheckoutError,
    CrossNetworkCheckoutService,
    CymedOrderPaymentItem,
    CyshopCartItem,
)
from products.cymed.core.commerce.serializers import CheckoutReceiptSerializer, CheckoutRequestSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cross_network_checkout(request):
    serializer = CheckoutRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data

    person = resolve_person_from_request(request, d.get("person_id"))
    if person is None:
        return Response(
            {"detail": "Could not resolve a CyID person for this request."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cymed_items = [
        CymedOrderPaymentItem(order_id=str(i["order_id"]), amount=i["amount"], description=i.get("description", ""))
        for i in d.get("cymed_items", [])
    ]
    cyshop_items = [
        CyshopCartItem(
            cyshop_tenant_id=str(i["cyshop_tenant_id"]),
            company_id=str(i["company_id"]),
            branch_id=str(i["branch_id"]),
            item_name=i["item_name"],
            qty=i["qty"],
            unit_price=i["unit_price"],
            description=i.get("description", ""),
        )
        for i in d.get("cyshop_items", [])
    ]

    try:
        receipt = CrossNetworkCheckoutService().checkout(
            person,
            d["currency"],
            cymed_items=cymed_items,
            cyshop_items=cyshop_items,
            cyid_token=d.get("cyid_token", ""),
            customer_name=d.get("customer_name", ""),
        )
    except InsufficientFundsError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    except CheckoutError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(CheckoutReceiptSerializer(receipt).data, status=status.HTTP_201_CREATED)
