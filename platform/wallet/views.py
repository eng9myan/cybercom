from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.wallet.serializers import (
    WalletDebitSerializer,
    WalletLedgerEntrySerializer,
    WalletTopUpSerializer,
)
from platform.wallet.services import InsufficientFundsError, WalletService, resolve_person_from_request

_resolve_person = resolve_person_from_request


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def wallet_topup(request):
    serializer = WalletTopUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data

    person = _resolve_person(request, d.get("person_id"))
    if person is None:
        return Response({"detail": "Could not resolve a CyID person for this request."}, status=status.HTTP_400_BAD_REQUEST)

    entry = WalletService().top_up(
        person, d["currency"], d["amount"], reference=d.get("reference", ""),
        created_by=str(getattr(request, "auth_claims", {}).get("sub", "")),
    )
    return Response(WalletLedgerEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def wallet_debit(request):
    serializer = WalletDebitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data

    person = _resolve_person(request, d.get("person_id"))
    if person is None:
        return Response({"detail": "Could not resolve a CyID person for this request."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        entry = WalletService().debit(
            person, d["currency"], d["amount"], reference=d.get("reference", ""),
            created_by=str(getattr(request, "auth_claims", {}).get("sub", "")),
        )
    except InsufficientFundsError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    return Response(WalletLedgerEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_balance(request):
    currency = request.query_params.get("currency")
    if not currency:
        return Response({"detail": "currency query param is required."}, status=status.HTTP_400_BAD_REQUEST)
    person = _resolve_person(request, request.query_params.get("person_id"))
    if person is None:
        return Response({"detail": "Could not resolve a CyID person for this request."}, status=status.HTTP_400_BAD_REQUEST)
    balance = WalletService.get_balance(person, currency)
    return Response({"person_id": str(person.id), "currency": currency, "balance": str(balance)})
