from django.urls import path

from products.cyed.erp.views import ErpProxyView

urlpatterns = [
    path("<path:path>", ErpProxyView.as_view(), name="erp-proxy"),
]
