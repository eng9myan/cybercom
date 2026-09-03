"""CyMed Pharmacy Compounding URL patterns."""
from django.urls import path

from .views import (
    CompoundingFormulationViewSet,
    CompoundingIngredientViewSet,
    CompoundingOrderViewSet,
    CompoundingStepViewSet,
    IngredientLotViewSet,
    QATestViewSet,
)


formulation_list = CompoundingFormulationViewSet.as_view({"get": "list", "post": "create"})
formulation_detail = CompoundingFormulationViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

ingredient_list = CompoundingIngredientViewSet.as_view({"get": "list", "post": "create"})
ingredient_detail = CompoundingIngredientViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

order_list = CompoundingOrderViewSet.as_view({"get": "list", "post": "create"})
order_detail = CompoundingOrderViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
order_create_order = CompoundingOrderViewSet.as_view({"post": "create_order"})
order_verify = CompoundingOrderViewSet.as_view({"post": "verify"})
order_record_step = CompoundingOrderViewSet.as_view({"post": "record_step"})
order_record_qa = CompoundingOrderViewSet.as_view({"post": "record_qa"})
order_release = CompoundingOrderViewSet.as_view({"post": "release"})
order_reject = CompoundingOrderViewSet.as_view({"post": "reject"})

step_list = CompoundingStepViewSet.as_view({"get": "list", "post": "create"})
step_detail = CompoundingStepViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

lot_list = IngredientLotViewSet.as_view({"get": "list", "post": "create"})
lot_detail = IngredientLotViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

qa_list = QATestViewSet.as_view({"get": "list", "post": "create"})
qa_detail = QATestViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)


urlpatterns = [
    path("formulations/", formulation_list, name="compounding-formulation-list"),
    path("formulations/<uuid:pk>/", formulation_detail, name="compounding-formulation-detail"),
    path("ingredients/", ingredient_list, name="compounding-ingredient-list"),
    path("ingredients/<uuid:pk>/", ingredient_detail, name="compounding-ingredient-detail"),
    path("orders/", order_list, name="compounding-order-list"),
    path("orders/<uuid:pk>/", order_detail, name="compounding-order-detail"),
    path("orders/create-order/", order_create_order, name="compounding-order-create"),
    path("orders/<uuid:pk>/verify/", order_verify, name="compounding-order-verify"),
    path("orders/<uuid:pk>/record-step/", order_record_step, name="compounding-order-record-step"),
    path("orders/<uuid:pk>/record-qa/", order_record_qa, name="compounding-order-record-qa"),
    path("orders/<uuid:pk>/release/", order_release, name="compounding-order-release"),
    path("orders/<uuid:pk>/reject/", order_reject, name="compounding-order-reject"),
    path("steps/", step_list, name="compounding-step-list"),
    path("steps/<uuid:pk>/", step_detail, name="compounding-step-detail"),
    path("ingredient-lots/", lot_list, name="compounding-lot-list"),
    path("ingredient-lots/<uuid:pk>/", lot_detail, name="compounding-lot-detail"),
    path("qa-tests/", qa_list, name="compounding-qa-list"),
    path("qa-tests/<uuid:pk>/", qa_detail, name="compounding-qa-detail"),
]
