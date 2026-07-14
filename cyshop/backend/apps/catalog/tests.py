from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.tenants.models import Tenant, Company, Branch
from .models import Category, ProductUnit, TaxClass, Product, KitComponent

User = get_user_model()
TENANT_ID = '018f1a2b-3c4d-7e5f-8a9b-0c1d2e3f4a5b'
# Use a long test key so PyJWT doesn't emit InsecureKeyLengthWarning
_TEST_SECRET = 'test-secret-key-that-is-long-enough-for-hs256-minimum-32-bytes'


def _make_tenant_and_company():
    tenant = Tenant.objects.create(name='Test Tenant', subdomain='test', tenant_id=TENANT_ID)
    company = Company.objects.create(name='Test Co', tenant_id=TENANT_ID)
    return tenant, company


def _auth_client(user):
    from apps.identity.authentication import JWTAuthentication
    import jwt, datetime
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'tenant_id': TENANT_ID,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    from django.conf import settings
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_TENANT_ID=TENANT_ID)
    return client


class CatalogApiTests(TestCase):

    def setUp(self):
        self.tenant, self.company = _make_tenant_and_company()
        self.user = User.objects.create_user(
            username='cataloguser', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)
        self.unit = ProductUnit.objects.create(
            name='Piece', abbreviation='PCS',
            company=self.company, tenant_id=TENANT_ID,
        )
        self.cat = Category.objects.create(
            name='Beverages', company=self.company, tenant_id=TENANT_ID,
        )

    def test_list_categories(self):
        res = self.client.get('/api/v1/catalog/categories/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]['name'], 'Beverages')

    def test_create_product(self):
        payload = {
            'name': 'Espresso',
            'internal_ref': 'ESP-001',
            'company': str(self.company.id),
            'category': str(self.cat.id),
            'unit': str(self.unit.id),
            'product_type': 'STORABLE',
            'sell_price': '3.5000',
            'cost_price': '1.2000',
            'track_stock': True,
            'pos_available': True,
        }
        res = self.client.post('/api/v1/catalog/products/', payload, format='json')
        self.assertEqual(res.status_code, 201, res.json())
        data = res.json()
        self.assertEqual(data['name'], 'Espresso')
        self.assertEqual(data['tenant_id'], TENANT_ID)

    def test_tenant_isolation(self):
        """A user from a different tenant cannot see this tenant's products."""
        Product.objects.create(
            name='Secret Product', company=self.company, tenant_id=TENANT_ID,
            sell_price='0', cost_price='0', product_type='STORABLE',
        )
        other_user = User.objects.create_user(username='other', password='x', tenant_id='00000000-0000-7000-0000-000000000001')
        other_tenant = Tenant.objects.create(name='Other', subdomain='other', tenant_id='00000000-0000-7000-0000-000000000001')
        other_client = APIClient()
        other_client.credentials(
            HTTP_AUTHORIZATION='Bearer invalid',
            HTTP_X_TENANT_ID='00000000-0000-7000-0000-000000000001',
        )
        # other tenant sees no products even if auth were valid
        qs = Product.objects.filter(tenant_id='00000000-0000-7000-0000-000000000001')
        self.assertEqual(qs.count(), 0)

    def test_product_list_search(self):
        Product.objects.create(
            name='Latte', internal_ref='LAT-001',
            company=self.company, tenant_id=TENANT_ID,
            sell_price='4.5', cost_price='1.5', product_type='STORABLE',
        )
        Product.objects.create(
            name='Pizza', internal_ref='PIZ-001',
            company=self.company, tenant_id=TENANT_ID,
            sell_price='12', cost_price='4', product_type='STORABLE',
        )
        res = self.client.get('/api/v1/catalog/products/?search=latt')
        self.assertEqual(res.status_code, 200)
        names = [p['name'] for p in res.json()]
        self.assertIn('Latte', names)
        self.assertNotIn('Pizza', names)

    def test_slug_auto_generated(self):
        cat = Category.objects.create(
            name='Hot Drinks', company=self.company, tenant_id=TENANT_ID,
        )
        self.assertEqual(cat.slug, 'hot-drinks')


class KitComponentTests(TestCase):

    def setUp(self):
        self.tenant, self.company = _make_tenant_and_company()
        self.user = User.objects.create_user(
            username='kituser', password='pass', tenant_id=TENANT_ID
        )
        self.client = _auth_client(self.user)
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

    def test_add_bom_component_via_api(self):
        res = self.client.post(
            f'/api/v1/catalog/products/{self.kit.id}/bom/',
            {'component_product': str(self.bun.id), 'quantity_per_unit': '1'},
            format='json',
        )
        self.assertEqual(res.status_code, 201, res.json())
        self.assertEqual(res.json()['component_product_name'], 'Burger Bun')

    def test_list_bom_components(self):
        KitComponent.objects.create(
            product=self.kit, component_product=self.bun, quantity_per_unit='1', tenant_id=TENANT_ID,
        )
        KitComponent.objects.create(
            product=self.kit, component_product=self.patty, quantity_per_unit='2', tenant_id=TENANT_ID,
        )
        res = self.client.get(f'/api/v1/catalog/products/{self.kit.id}/bom/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)

    def test_component_cannot_be_itself(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            KitComponent.objects.create(
                product=self.kit, component_product=self.kit, quantity_per_unit='1', tenant_id=TENANT_ID,
            )

    def test_quantity_must_be_positive(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            KitComponent.objects.create(
                product=self.kit, component_product=self.bun, quantity_per_unit='0', tenant_id=TENANT_ID,
            )
