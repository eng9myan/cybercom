import io
from datetime import date

import pytest
from django.core.management import call_command

from platform.common.tenant_context import tenant_context
from products.cymed.simulations.engine import HospitalSimulator
from products.cymed.simulations.kpis import HospitalKpis
from products.cymed.simulations.models import SimulationRun

START = date(2026, 3, 2)


def _run(**kw):
    kw.setdefault("seed", 5)
    kw.setdefault("start_date", START)
    kw.setdefault("days", 3)
    kw.setdefault("scale", 0.2)
    return HospitalSimulator(**kw).run()


class TestEngine:
    def test_deterministic(self):
        a, b = _run(), _run()
        assert len(a.ed_visits) == len(b.ed_visits)
        assert len(a.stays) == len(b.stays)
        assert sum(o.cost for v in a.ed_visits for o in v.orders) == \
               pytest.approx(sum(o.cost for v in b.ed_visits for o in v.orders))

    def test_produces_all_activity(self):
        r = _run()
        assert r.ed_visits and r.clinic_visits and r.stays
        assert all(v.dispo_utc >= v.arrival_utc for v in r.ed_visits)
        assert all(s.discharge_utc > s.admit_utc for s in r.stays)
        assert all(0 <= s.boarding_min <= 720 for s in r.stays)

    def test_orders_result_after_ordered(self):
        r = _run()
        allo = ([o for v in r.ed_visits for o in v.orders]
                + [o for s in r.stays for o in s.orders])
        assert allo
        assert all(o.resulted_utc >= o.ordered_utc for o in allo)

    def test_ed_surge_raises_volume_and_lwbs(self):
        base = _run(variant="baseline", days=5, scale=0.5)
        surge = _run(variant="ed_surge", days=5, scale=0.5)
        assert len(surge.ed_visits) > len(base.ed_visits) * 1.15
        b_lwbs = sum(1 for v in base.ed_visits if v.disposition == "lwbs") / len(base.ed_visits)
        s_lwbs = sum(1 for v in surge.ed_visits if v.disposition == "lwbs") / len(surge.ed_visits)
        assert s_lwbs >= b_lwbs

    def test_ct_downtime_slows_imaging(self):
        base = HospitalKpis(_run(variant="baseline", days=6, scale=0.6)).summary()
        down = HospitalKpis(_run(variant="imaging_ct_downtime", days=6, scale=0.6)).summary()
        assert down["orders"]["by_kind"]["imaging"]["avg_tat_min"] > \
               base["orders"]["by_kind"]["imaging"]["avg_tat_min"]


class TestKpis:
    def test_summary_shape(self):
        s = HospitalKpis(_run()).summary()
        for k in ("emergency", "inpatient", "orders", "clinics", "by_service_line",
                  "wards", "by_day", "csat_proxy"):
            assert k in s
        assert 0 <= s["emergency"]["admit_rate"] <= 100
        assert 0 <= s["inpatient"]["bed_occupancy_pct"] <= 130
        assert len(s["by_day"]) == _run().days


@pytest.mark.django_db
class TestSeeder:
    def _seed(self):
        out = io.StringIO()
        call_command("seed_hospital_sim", wipe=True, no_files=True, seed=3,
                     start_date=START.isoformat(), days=2, scale=0.12,
                     slug="cymed-hosp-test", stdout=out)
        return out.getvalue()

    def test_writes_clinical_records(self):
        from platform.tenant.models import Tenant
        from products.cymed.core.encounters.models import Encounter
        from products.cymed.core.facilities.models import Bed
        from products.cymed.core.orders.models import Order
        from products.cymed.core.scheduling.models import Appointment
        from products.cymed.hospital.adt.models import Admission
        from products.cymed.hospital.emergency.models import EmergencyVisit
        from products.cymed.hospital.inpatient.models import HospitalStay

        self._seed()
        t = Tenant.objects.get(slug="cymed-hosp-test")
        tid = t.id
        assert Bed.objects.filter(tenant_id=tid).count() > 100
        assert EmergencyVisit.objects.filter(tenant_id=tid).count() > 10
        assert Admission.objects.filter(tenant_id=tid).count() > 0
        assert HospitalStay.objects.filter(tenant_id=tid).count() == \
               Admission.objects.filter(tenant_id=tid).count()
        assert Encounter.objects.filter(tenant_id=tid).count() > 20
        assert Order.objects.filter(tenant_id=tid).count() > 20
        assert Appointment.objects.filter(tenant_id=tid).count() > 0

        run = SimulationRun.objects.filter(scenario="hospital:baseline").latest("created_at")
        assert run.status == "COMPLETED"
        assert run.summary["emergency"]["visits"] == \
               EmergencyVisit.objects.filter(tenant_id=tid).count()

    def test_phi_encrypted_field_roundtrips(self):
        from platform.tenant.models import Tenant
        from products.cymed.hospital.emergency.models import EmergencyVisit

        self._seed()
        tid = Tenant.objects.get(slug="cymed-hosp-test").id
        with tenant_context(tid):
            v = EmergencyVisit.objects.filter(tenant_id=tid).first()
            assert v.presenting_complaint
            assert "/" in v.presenting_complaint or len(v.presenting_complaint) > 3

    def test_wipe_makes_rerun_idempotent(self):
        from platform.tenant.models import Tenant
        from products.cymed.hospital.emergency.models import EmergencyVisit
        self._seed()
        tid = Tenant.objects.get(slug="cymed-hosp-test").id
        first = EmergencyVisit.objects.filter(tenant_id=tid).count()
        self._seed()
        assert EmergencyVisit.objects.filter(tenant_id=tid).count() == first
