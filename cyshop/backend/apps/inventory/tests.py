from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.tenants.models import Company, Branch, Tenant
from apps.catalog.models import Product, ProductUnit
from .models import Warehouse, StockLocation, StockLevel, StockMovement, StockTransfer

User = get_user_model()
TENANT_ID = '018f1a2b-3c4d-7e5f-8a9b-0c1d2e3f4a5c'


def _setup_base():
    tenant = Tenant.objects.create(name='Inv Tenant', subdomain='inv', tenant_id=TENANT_ID)
    company = Company.objects.create(name='Inv Co', tenant_id=TENANT_ID)
    branch = Branch.objects.create(name='Main Branch', company=company, tenant_id=TENANT_ID, address='HQ')
    unit = ProductUnit.objects.create(name='Piece', abbreviation='PCS', company=company, tenant_id=TENANT_ID)
    warehouse = Warehouse.objects.create(
        name='Main Warehouse', code='WH-MAIN',
        company=company, branch=branch, tenant_id=TENANT_ID,
    )
    location_in = StockLocation.objects.create(
        name='Receiving', code='RCV',
        warehouse=warehouse, location_type='RECEIVING', tenant_id=TENANT_ID,
    )
    location_shelf = StockLocation.objects.create(
        name='Shelf A1', code='SHELF-A1',
        warehouse=warehouse, location_type='INTERNAL', tenant_id=TENANT_ID,
    )
    product = Product.objects.create(
        name='Test Coffee', internal_ref='TCF-001',
        company=company, unit=unit, tenant_id=TENANT_ID,
        sell_price='5.00', cost_price='1.50', product_type='STORABLE',
    )
    return company, branch, warehouse, location_in, location_shelf, product


class StockMovementTests(TestCase):

    def setUp(self):
        self.company, self.branch, self.warehouse, self.loc_in, self.loc_shelf, self.product = _setup_base()

    def test_receipt_creates_stock_level(self):
        StockMovement.objects.create(
            product=self.product,
            to_location=self.loc_in,
            quantity=Decimal('100'),
            movement_type='RECEIPT',
            reference='PO-001',
            tenant_id=TENANT_ID,
        )
        level = StockLevel.objects.get(product=self.product, location=self.loc_in)
        self.assertEqual(level.quantity, Decimal('100'))

    def test_transfer_debits_source_credits_destination(self):
        # Receive 50 units first
        StockMovement.objects.create(
            product=self.product, to_location=self.loc_in,
            quantity=Decimal('50'), movement_type='RECEIPT', tenant_id=TENANT_ID,
        )
        # Transfer 20 from receiving to shelf
        StockMovement.objects.create(
            product=self.product,
            from_location=self.loc_in,
            to_location=self.loc_shelf,
            quantity=Decimal('20'),
            movement_type='TRANSFER',
            tenant_id=TENANT_ID,
        )
        level_in = StockLevel.objects.get(product=self.product, location=self.loc_in)
        level_shelf = StockLevel.objects.get(product=self.product, location=self.loc_shelf)
        self.assertEqual(level_in.quantity, Decimal('30'))
        self.assertEqual(level_shelf.quantity, Decimal('20'))

    def test_issue_reduces_stock(self):
        StockMovement.objects.create(
            product=self.product, to_location=self.loc_shelf,
            quantity=Decimal('10'), movement_type='RECEIPT', tenant_id=TENANT_ID,
        )
        StockMovement.objects.create(
            product=self.product, from_location=self.loc_shelf,
            quantity=Decimal('3'), movement_type='ISSUE', tenant_id=TENANT_ID,
        )
        level = StockLevel.objects.get(product=self.product, location=self.loc_shelf)
        self.assertEqual(level.quantity, Decimal('7'))

    def test_movement_requires_at_least_one_location(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                product=self.product,
                quantity=Decimal('5'),
                movement_type='ADJUSTMENT',
                tenant_id=TENANT_ID,
            )

    def test_movement_quantity_must_be_positive(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                product=self.product,
                to_location=self.loc_shelf,
                quantity=Decimal('-1'),
                movement_type='RECEIPT',
                tenant_id=TENANT_ID,
            )

    def test_movement_is_immutable_via_api(self):
        user = User.objects.create_user(username='invuser', password='x', tenant_id=TENANT_ID)
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
        mv = StockMovement.objects.create(
            product=self.product, to_location=self.loc_shelf,
            quantity=Decimal('5'), movement_type='RECEIPT', tenant_id=TENANT_ID,
        )
        res = client.patch(f'/api/v1/inventory/movements/{mv.id}/', {'quantity': '99'}, format='json')
        self.assertEqual(res.status_code, 405)

    def test_stock_level_summary_endpoint(self):
        user = User.objects.create_user(username='sumuser', password='x', tenant_id=TENANT_ID)
        import jwt, datetime
        from django.conf import settings
        payload = {
            'user_id': str(user.id), 'username': user.username,
            'tenant_id': TENANT_ID,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_TENANT_ID=TENANT_ID)
        StockMovement.objects.create(
            product=self.product, to_location=self.loc_shelf,
            quantity=Decimal('15'), movement_type='RECEIPT', tenant_id=TENANT_ID,
        )
        res = client.get('/api/v1/inventory/levels/summary/')
        self.assertEqual(res.status_code, 200)
        totals = {item['product__name']: item['total_qty'] for item in res.json()}
        self.assertIn('Test Coffee', totals)


class StockTransferTests(TestCase):

    def setUp(self):
        self.company, self.branch_a, self.warehouse_a, self.loc_a, _, self.product = _setup_base()
        self.branch_b = Branch.objects.create(
            name='Second Branch', company=self.company, tenant_id=TENANT_ID, address='Branch B'
        )
        self.warehouse_b = Warehouse.objects.create(
            name='Second Warehouse', code='WH-B',
            company=self.company, branch=self.branch_b, tenant_id=TENANT_ID,
        )
        self.loc_b = StockLocation.objects.create(
            name='Receiving B', code='RCV-B',
            warehouse=self.warehouse_b, location_type='RECEIVING', tenant_id=TENANT_ID,
        )
        StockMovement.objects.create(
            product=self.product, to_location=self.loc_a,
            quantity=Decimal('50'), movement_type='RECEIPT', tenant_id=TENANT_ID,
        )

    def test_dispatch_debits_source_only(self):
        transfer = StockTransfer.objects.create(
            company=self.company, from_branch=self.branch_a, to_branch=self.branch_b,
            from_location=self.loc_a, to_location=self.loc_b,
            product=self.product, quantity=Decimal('20'), tenant_id=TENANT_ID,
        )
        transfer.dispatch()
        source_level = StockLevel.objects.get(product=self.product, location=self.loc_a)
        self.assertEqual(source_level.quantity, Decimal('30'))
        self.assertFalse(StockLevel.objects.filter(product=self.product, location=self.loc_b).exists())
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, 'IN_TRANSIT')

    def test_receive_credits_destination(self):
        transfer = StockTransfer.objects.create(
            company=self.company, from_branch=self.branch_a, to_branch=self.branch_b,
            from_location=self.loc_a, to_location=self.loc_b,
            product=self.product, quantity=Decimal('20'), tenant_id=TENANT_ID,
        )
        transfer.dispatch()
        transfer.receive()
        dest_level = StockLevel.objects.get(product=self.product, location=self.loc_b)
        self.assertEqual(dest_level.quantity, Decimal('20'))
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, 'COMPLETED')

    def test_cannot_receive_before_dispatch(self):
        from django.core.exceptions import ValidationError
        transfer = StockTransfer.objects.create(
            company=self.company, from_branch=self.branch_a, to_branch=self.branch_b,
            from_location=self.loc_a, to_location=self.loc_b,
            product=self.product, quantity=Decimal('20'), tenant_id=TENANT_ID,
        )
        with self.assertRaises(ValidationError):
            transfer.receive()

    def test_transfer_number_auto_generated(self):
        transfer = StockTransfer.objects.create(
            company=self.company, from_branch=self.branch_a, to_branch=self.branch_b,
            from_location=self.loc_a, to_location=self.loc_b,
            product=self.product, quantity=Decimal('5'), tenant_id=TENANT_ID,
        )
        self.assertTrue(transfer.transfer_number.startswith('TRF-'))

    def test_dispatch_api_endpoint(self):
        user = User.objects.create_user(username='trfuser', password='x', tenant_id=TENANT_ID)
        import jwt, datetime
        from django.conf import settings
        payload = {
            'user_id': str(user.id), 'username': user.username,
            'tenant_id': TENANT_ID,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_TENANT_ID=TENANT_ID)
        transfer = StockTransfer.objects.create(
            company=self.company, from_branch=self.branch_a, to_branch=self.branch_b,
            from_location=self.loc_a, to_location=self.loc_b,
            product=self.product, quantity=Decimal('10'), tenant_id=TENANT_ID,
        )
        res = client.post(f'/api/v1/inventory/transfers/{transfer.id}/dispatch/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'IN_TRANSIT')
        res2 = client.post(f'/api/v1/inventory/transfers/{transfer.id}/receive/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()['status'], 'COMPLETED')
