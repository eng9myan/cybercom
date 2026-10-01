from django.urls import path

from .views import ExplodeRecipesView, PlanBasketView, PurchaseView, ReplenishView

urlpatterns = [
    path("purchases/", PurchaseView.as_view(), name="pantry-purchases"),
    path("replenish/", ReplenishView.as_view(), name="pantry-replenish"),
    path("recipes/explode/", ExplodeRecipesView.as_view(), name="pantry-recipes-explode"),
    path("plan-basket/", PlanBasketView.as_view(), name="pantry-plan-basket"),
]
