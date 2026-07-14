from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.tenants.models import Tenant, Company, Branch
from apps.catalog.models import TaxClass, Product, KitComponent
from .models import PosSession, PosOrder, PosOrderLine, PosPayment, PosReceipt, Device

User = get_user_model()
TENANT_ID = '018f1a2b-3c4d-7e5f-0000-0c1d2e3f4a5b'
OTHER_TENANT = '00000000-0000-7000-0001-000000000002'


def _setup_tenant():
    tenant = Tenant.objects.create(name='POS Tenant', subdomain='pos-test', tenant_id=TENANT_ID)
    company = Company.objects.create(name='POS Co', tenant_id=TENANT_ID)
    branch = Branch.objects.create(
        name='Main Branch', company=company, tenant_id=TENANT_ID, address='123 St'
    )
    return tenant, company, branch


def _auth_client(user):
    import jwt, datetime
    from django.conf import settings
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'tenant_id': TENANT_ID,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_TENANT_ID=TENANT_ID)
    return client


class PosSessionTests(TestCase):
    def setUp(self):
        self.tenant, self.company, self.branch = _setup_tenant()
        self.user = User.objects.create_user(
            username='cashier1', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)

    def test_open_session(self):
        payload = {
            'company': str(self.company.id),
            'branch': str(self.branch.id),
            'cashier': str(self.user.id),
            'opening_float': '50.0000',
        }
        res = self.client.post('/api/v1/pos/sessions/', payload, format='json')
        self.assertEqual(res.status_code, 201, res.json())
        data = res.json()
        self.assertEqual(data['status'], 'OPEN')
        self.assertTrue(data['name'].startswith('Session #'))

    def test_close_session(self):
        session = PosSession.objects.create(
            company=self.company,
            branch=self.branch,
            cashier=self.user,
            tenant_id=TENANT_ID,
        )
        res = self.client.post(
            f'/api/v1/pos/sessions/{session.id}/close/',
            {'closing_float': '48.5000'},
            format='json',
        )
        self.assertEqual(res.status_code, 200, res.json())
        self.assertEqual(res.json()['status'], 'CLOSED')


class PosOrderTests(TestCase):
    def setUp(self):
        self.tenant, self.company, self.branch = _setup_tenant()
        self.user = User.objects.create_user(
            username='cashier2', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)
        self.tax = TaxClass.objects.create(
            name='Standard', code='STD', company=self.company,
            tenant_id=TENANT_ID, rate='0.1600',
        )
        self.product = Product.objects.create(
            name='Espresso', company=self.company, tenant_id=TENANT_ID,
            sell_price='3.5000', cost_price='1.2000', product_type='STORABLE',
            tax_class=self.tax,
        )
        self.session = PosSession.objects.create(
            company=self.company, branch=self.branch,
            cashier=self.user, tenant_id=TENANT_ID,
        )

    def _order_payload(self, **kwargs):
        return {
            'company': str(self.company.id),
            'session': str(self.session.id),
            'lines_input': [
                {'product': str(self.product.id), 'quantity': '2'},
            ],
            **kwargs,
        }

    def test_create_order_with_lines(self):
        res = self.client.post('/api/v1/pos/orders/', self._order_payload(), format='json')
        self.assertEqual(res.status_code, 201, res.json())
        data = res.json()
        self.assertEqual(data['status'], 'DRAFT')
        self.assertEqual(len(data['lines']), 1)
        self.assertNotEqual(data['order_number'], '')

    def test_order_totals_correct(self):
        res = self.client.post('/api/v1/pos/orders/', self._order_payload(), format='json')
        self.assertEqual(res.status_code, 201, res.json())
        data = res.json()
        # 2 × 3.5 = 7.00 subtotal; 7.00 × 0.16 = 1.12 tax; total = 8.12
        self.assertAlmostEqual(float(data['subtotal']), 7.0, places=2)
        self.assertAlmostEqual(float(data['tax_amount']), 1.12, places=2)
        self.assertAlmostEqual(float(data['total']), 8.12, places=2)

    def test_pay_order_creates_receipt(self):
        res = self.client.post('/api/v1/pos/orders/', self._order_payload(), format='json')
        order_id = res.json()['id']
        total = res.json()['total']

        pay_res = self.client.post(
            f'/api/v1/pos/orders/{order_id}/pay/',
            {'method': 'CASH', 'amount': str(Decimal(total) + 2), 'change_given': '2.0000'},
            format='json',
        )
        self.assertEqual(pay_res.status_code, 200, pay_res.json())
        data = pay_res.json()
        self.assertEqual(data['status'], 'PAID')
        self.assertIsNotNone(data['receipt'])
        self.assertTrue(data['receipt']['receipt_number'].startswith('REC-'))

    def test_cancel_paid_order_rejected(self):
        res = self.client.post('/api/v1/pos/orders/', self._order_payload(), format='json')
        order_id = res.json()['id']
        total = res.json()['total']
        self.client.post(
            f'/api/v1/pos/orders/{order_id}/pay/',
            {'method': 'CASH', 'amount': total, 'change_given': '0'},
            format='json',
        )
        cancel_res = self.client.post(f'/api/v1/pos/orders/{order_id}/cancel/')
        self.assertEqual(cancel_res.status_code, 400)

    def test_cancel_draft_order(self):
        res = self.client.post('/api/v1/pos/orders/', self._order_payload(), format='json')
        order_id = res.json()['id']
        cancel_res = self.client.post(f'/api/v1/pos/orders/{order_id}/cancel/')
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json()['status'], 'CANCELLED')

    def test_tenant_isolation(self):
        PosOrder.objects.create(
            company=self.company, tenant_id=TENANT_ID,
            order_number='ORD-ISOLATION',
        )
        count_own = PosOrder.objects.filter(tenant_id=TENANT_ID).count()
        count_other = PosOrder.objects.filter(tenant_id=OTHER_TENANT).count()
        self.assertGreater(count_own, 0)
        self.assertEqual(count_other, 0)

    def test_confirm_empty_order_rejected(self):
        empty = PosOrder.objects.create(
            company=self.company, tenant_id=TENANT_ID,
            cashier=self.user, session=self.session,
        )
        res = self.client.post(f'/api/v1/pos/orders/{empty.id}/confirm/')
        self.assertEqual(res.status_code, 400)


class AutoDeKitTests(TestCase):
    def setUp(self):
        self.tenant, self.company, self.branch = _setup_tenant()
        self.user = User.objects.create_user(
            username='dekituser', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)

        from apps.inventory.models import Warehouse, StockLocation, StockMovement  # noqa: PLC0415
        self.warehouse = Warehouse.objects.create(
            company=self.company, branch=self.branch, tenant_id=TENANT_ID,
            name='Main Warehouse', code='WH-MAIN',
        )
        self.location = StockLocation.objects.create(
            warehouse=self.warehouse, tenant_id=TENANT_ID,
            name='Shelf', code='SHELF', location_type='INTERNAL',
        )

        self.kit = Product.objects.create(
            name='Burger Combo', internal_ref='KIT-001', company=self.company, tenant_id=TENANT_ID,
            sell_price='9.99', cost_price='4.00', product_type='KIT',
        )
        self.bun = Product.objects.create(
            name='Burger Bun', internal_ref='BUN-001', company=self.company, tenant_id=TENANT_ID,
            sell_price='0.50', cost_price='0.20', product_type='STORABLE',
        )
        self.patty = Product.objects.create(
            name='Beef Patty', internal_ref='PATTY-001', company=self.company, tenant_id=TENANT_ID,
            sell_price='2.00', cost_price='1.00', product_type='STORABLE',
        )
        KitComponent.objects.create(
            product=self.kit, component_product=self.bun, quantity_per_unit='1', tenant_id=TENANT_ID,
        )
        KitComponent.objects.create(
            product=self.kit, component_product=self.patty, quantity_per_unit='2', tenant_id=TENANT_ID,
        )

        # Opening stock so the deduction has something to draw down from.
        StockMovement.objects.create(
            product=self.bun, to_location=self.location, quantity='50',
            movement_type='OPENING', tenant_id=TENANT_ID,
        )
        StockMovement.objects.create(
            product=self.patty, to_location=self.location, quantity='50',
            movement_type='OPENING', tenant_id=TENANT_ID,
        )

        self.session = PosSession.objects.create(
            company=self.company, branch=self.branch, cashier=self.user, tenant_id=TENANT_ID,
        )

    def test_paying_kit_order_deducts_components(self):
        from apps.inventory.models import StockLevel  # noqa: PLC0415

        order_payload = {
            'company': str(self.company.id),
            'branch': str(self.branch.id),
            'session': str(self.session.id),
            'lines_input': [{'product': str(self.kit.id), 'quantity': '3'}],
        }
        res = self.client.post('/api/v1/pos/orders/', order_payload, format='json')
        self.assertEqual(res.status_code, 201, res.json())
        order_id = res.json()['id']
        total = res.json()['total']

        pay_res = self.client.post(
            f'/api/v1/pos/orders/{order_id}/pay/',
            {'method': 'CASH', 'amount': total, 'change_given': '0'},
            format='json',
        )
        self.assertEqual(pay_res.status_code, 200, pay_res.json())

        # 3 combos x 1 bun each = 3 buns issued; 3 combos x 2 patties each = 6 patties issued.
        bun_level = StockLevel.objects.get(product=self.bun, location=self.location)
        patty_level = StockLevel.objects.get(product=self.patty, location=self.location)
        self.assertEqual(bun_level.quantity, Decimal('47'))
        self.assertEqual(patty_level.quantity, Decimal('44'))

    def test_non_kit_order_does_not_deduct(self):
        order_payload = {
            'company': str(self.company.id),
            'branch': str(self.branch.id),
            'session': str(self.session.id),
            'lines_input': [{'product': str(self.bun.id), 'quantity': '5'}],
        }
        res = self.client.post('/api/v1/pos/orders/', order_payload, format='json')
        order_id = res.json()['id']
        total = res.json()['total']
        self.client.post(
            f'/api/v1/pos/orders/{order_id}/pay/',
            {'method': 'CASH', 'amount': total, 'change_given': '0'},
            format='json',
        )
        from apps.inventory.models import StockLevel  # noqa: PLC0415
        bun_level = StockLevel.objects.get(product=self.bun, location=self.location)
        self.assertEqual(bun_level.quantity, Decimal('50'))


class DeviceTests(TestCase):
    def setUp(self):
        self.tenant, self.company, self.branch = _setup_tenant()
        self.user = User.objects.create_user(
            username='devadmin', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)

    def test_register_device(self):
        payload = {
            'company': str(self.company.id),
            'branch': str(self.branch.id),
            'name': 'Kitchen Display 1',
            'code': 'KDS-01',
            'device_type': 'KDS',
        }
        res = self.client.post('/api/v1/pos/devices/', payload, format='json')
        self.assertEqual(res.status_code, 201, res.json())
        data = res.json()
        self.assertEqual(data['route'], '/kds')
        self.assertEqual(data['device_type_display'], 'Kitchen Display')

    def test_heartbeat_updates_last_seen(self):
        device = Device.objects.create(
            company=self.company, branch=self.branch, tenant_id=TENANT_ID,
            name='POS 1', code='POS-01', device_type='POS',
        )
        self.assertIsNone(device.last_seen_at)
        res = self.client.post(f'/api/v1/pos/devices/{device.id}/heartbeat/')
        self.assertEqual(res.status_code, 200, res.json())
        self.assertIsNotNone(res.json()['last_seen_at'])

    def test_device_code_unique_per_company(self):
        from django.db import IntegrityError, transaction as db_transaction
        Device.objects.create(
            company=self.company, branch=self.branch, tenant_id=TENANT_ID,
            name='POS 1', code='DUP', device_type='POS',
        )
        with self.assertRaises(IntegrityError):
            with db_transaction.atomic():
                Device.objects.create(
                    company=self.company, branch=self.branch, tenant_id=TENANT_ID,
                    name='POS 2', code='DUP', device_type='POS',
                )


class KitchenStatusTests(TestCase):
    def setUp(self):
        self.tenant, self.company, self.branch = _setup_tenant()
        self.user = User.objects.create_user(
            username='kdsuser', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)
        self.order = PosOrder.objects.create(
            company=self.company, branch=self.branch, tenant_id=TENANT_ID,
            cashier=self.user,
        )

    def test_default_kitchen_status_pending(self):
        self.assertEqual(self.order.kitchen_status, 'PENDING')

    def test_set_kitchen_status(self):
        res = self.client.post(
            f'/api/v1/pos/orders/{self.order.id}/kitchen-status/',
            {'kitchen_status': 'READY'}, format='json',
        )
        self.assertEqual(res.status_code, 200, res.json())
        self.assertEqual(res.json()['kitchen_status'], 'READY')

    def test_invalid_kitchen_status_rejected(self):
        res = self.client.post(
            f'/api/v1/pos/orders/{self.order.id}/kitchen-status/',
            {'kitchen_status': 'BOGUS'}, format='json',
        )
        self.assertEqual(res.status_code, 400)
