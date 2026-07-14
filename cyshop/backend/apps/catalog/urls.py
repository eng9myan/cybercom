from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductUnitViewSet, TaxClassViewSet, ProductViewSet,
    ProductVariantViewSet, KitComponentViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'units', ProductUnitViewSet, basename='product-unit')
router.register(r'tax-classes', TaxClassViewSet, basename='tax-class')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='product-variant')
router.register(r'kit-components', KitComponentViewSet, basename='kit-component')

urlpatterns = router.urls
