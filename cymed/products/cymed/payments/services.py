"""High-level services orchestrating gateways + insurers + models."""
from decimal import Decimal
from uuid import UUID

from django.utils import timezone

from .gateways import get_gateway
from .insurers import get_insurer
from .models import (
    EligibilityCheck,
    InsurancePolicy,
    PaymentMethod,
    PaymentTransaction,
    PreAuthorization,
    UnifiedBill,
)


def check_eligibility(policy_id: UUID, service_code: str,
                      provider_tenant_id: UUID | None = None) -> EligibilityCheck:
    policy = InsurancePolicy.objects.get(id=policy_id)
    ins = get_insurer(policy.insurer_code, policy.profile.preferred_language and "SA")
    result = ins.eligibility(policy, service_code, provider_tenant_id)
    return EligibilityCheck.objects.create(
        tenant_id=policy.tenant_id,
        policy=policy,
        service_code=service_code,
        provider_tenant_id=provider_tenant_id,
        covered=result.covered,
        co_pay_amount=result.co_pay_amount,
        requires_preauth=result.requires_preauth,
        raw_response=result.raw,
    )


def submit_preauth(policy_id: UUID, service_code: str, justification: str,
                    provider_tenant_id: UUID) -> PreAuthorization:
    policy = InsurancePolicy.objects.get(id=policy_id)
    ins = get_insurer(policy.insurer_code)
    r = ins.preauth_submit(policy, service_code, justification, provider_tenant_id)
    return PreAuthorization.objects.create(
        tenant_id=policy.tenant_id,
        policy=policy,
        provider_tenant_id=provider_tenant_id,
        service_code=service_code,
        clinical_justification=justification,
        status=r.status,
        reference_number=r.reference_number,
        approved_amount=r.approved_amount,
        raw_response=r.raw,
    )


def pay_bill(bill_id: UUID, method_id: UUID, payer_profile_id: UUID,
             amount: Decimal | None = None,
             on_behalf_note: str = "",
             delegation_id: UUID | None = None) -> PaymentTransaction:
    bill = UnifiedBill.objects.get(id=bill_id)
    method = PaymentMethod.objects.get(id=method_id, profile_id=payer_profile_id)
    charge_amount = amount if amount is not None else bill.patient_due

    gateway = get_gateway(method.gateway)
    result = gateway.charge(
        token=method.gateway_token,
        amount=charge_amount,
        currency="SAR",
        metadata={"bill_number": bill.bill_number, "payer_id": str(payer_profile_id)},
    )

    txn = PaymentTransaction.objects.create(
        tenant_id=bill.tenant_id,
        bill=bill,
        payer_profile_id=payer_profile_id,
        payee_profile_id=bill.patient_profile_id,
        payment_method=method,
        amount=charge_amount,
        currency="SAR",
        method_type=method.type,
        status=result.status,
        gateway_reference=result.gateway_reference,
        gateway_raw=result.raw,
        on_behalf_note=on_behalf_note,
        delegation_id=delegation_id,
        completed_at=timezone.now() if result.success else None,
    )

    if result.success:
        # `txn` (just created, status="succeeded") is already included here — do not
        # add charge_amount again. The patient can only settle `patient_due`, not the
        # insurance-covered portion, so compare against that, not `total`.
        paid_so_far = sum(
            (t.amount for t in bill.transactions.filter(status="succeeded")), Decimal("0")
        )
        if paid_so_far >= bill.patient_due:
            bill.status = "paid"
            bill.paid_at = timezone.now()
        else:
            bill.status = "partial"
        bill.save(update_fields=["status", "paid_at", "updated_at"])

    return txn
