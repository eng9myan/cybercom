from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish(tenant_id, event_type, payload):
    try:
        from platform.events.outbox import OutboxEvent
        OutboxEvent.publish(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _notify_cyconnect(tenant_id, event_type, payload):
    """Push real-time alerts to clinicians via CyConnect (SMS/Push/Voice)."""
    try:
        from platform.integrations.hub import CyIntegrationHub
        CyIntegrationHub.send(
            tenant_id=tenant_id,
            destination="cyconnect",
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass


def _sync_cycom(tenant_id, event_type, payload):
    """Emit timesheet/payroll events to CyCom Payroll via CyIntegrationHub."""
    try:
        from platform.integrations.hub import CyIntegrationHub
        CyIntegrationHub.send(
            tenant_id=tenant_id,
            destination="cycom_payroll",
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass


@receiver(post_save, sender="cymed_hwm_scheduling.RosterSlot")
def on_roster_slot_completed(sender, instance, created, **kwargs):
    if not created and instance.status == "completed" and instance.checked_out_at:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.roster.hours_worked",
            payload={
                "slot_id": str(instance.id),
                "workforce_profile_id": str(instance.workforce_profile_id),
                "roster_cycle_id": str(instance.roster_cycle_id),
                "checked_in_at": instance.checked_in_at.isoformat() if instance.checked_in_at else None,
                "checked_out_at": instance.checked_out_at.isoformat(),
            },
        )
        _sync_cycom(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.roster.hours_worked",
            payload={
                "slot_id": str(instance.id),
                "workforce_profile_id": str(instance.workforce_profile_id),
                "checked_out_at": instance.checked_out_at.isoformat(),
            },
        )


@receiver(post_save, sender="cymed_hwm_swaps.ShiftSwapRequest")
def on_swap_committed(sender, instance, created, **kwargs):
    if not created and instance.status == "committed":
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.swap.committed",
            payload={
                "swap_id": str(instance.id),
                "requester_profile_id": str(instance.requester_profile_id),
                "recipient_profile_id": str(instance.recipient_profile_id),
            },
        )


@receiver(post_save, sender="cymed_hwm_float_pool.StaffingShortageAlert")
def on_shortage_alert(sender, instance, created, **kwargs):
    if created:
        _notify_cyconnect(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.shortage.alert",
            payload={
                "alert_id": str(instance.id),
                "department_id": str(instance.department_id),
                "escalation_level": instance.escalation_level,
            },
        )
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.shortage.alert",
            payload={
                "alert_id": str(instance.id),
                "department_id": str(instance.department_id),
                "escalation_level": instance.escalation_level,
                "diversion_activated": instance.diversion_activated,
            },
        )


@receiver(post_save, sender="cymed_hwm_oncall.OnCallPage")
def on_oncall_page_triggered(sender, instance, created, **kwargs):
    if created:
        _notify_cyconnect(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.oncall.page",
            payload={
                "page_id": str(instance.id),
                "urgency": instance.urgency,
                "roster_id": str(instance.oncall_roster_id),
                "ward_id": str(instance.initiating_ward_id),
                "sla_deadline": instance.sla_deadline.isoformat() if instance.sla_deadline else None,
            },
        )


@receiver(post_save, sender="cymed_hwm_oncall.OnCallEscalation")
def on_oncall_escalation(sender, instance, created, **kwargs):
    if created:
        _notify_cyconnect(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.oncall.escalation",
            payload={
                "escalation_id": str(instance.id),
                "page_id": str(instance.page_id),
                "escalation_level": instance.escalation_level,
                "escalated_to": str(instance.escalated_to_profile_id),
            },
        )
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.oncall.escalation",
            payload={
                "escalation_id": str(instance.id),
                "escalation_level": instance.escalation_level,
            },
        )


@receiver(post_save, sender="cymed_hwm_fatigue.FatigueViolation")
def on_fatigue_violation(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.fatigue.violation",
            payload={
                "violation_id": str(instance.id),
                "workforce_profile_id": str(instance.workforce_profile_id),
                "violation_type": instance.violation_type,
                "prescribing_authority_revoked": instance.prescribing_authority_revoked,
            },
        )


@receiver(post_save, sender="cymed_hwm_profiles.WorkforceProfile")
def on_profile_deactivated(sender, instance, created, **kwargs):
    if not created and not instance.is_active:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.hwm.profile.deactivated",
            payload={
                "employee_id": str(instance.employee_id),
                "profile_id": str(instance.id),
            },
        )
