from django.urls import path
from . import views

urlpatterns = [
    path("", views.PurchaseOrderListView.as_view(), name="po-list"),
    path("<uuid:pk>/", views.PurchaseOrderDetailView.as_view(), name="po-detail"),
    path("lines/", views.POLineListView.as_view(), name="po-line-list"),
    path("lines/<uuid:pk>/", views.POLineDetailView.as_view(), name="po-line-detail"),
    path("receipts/", views.GoodsReceiptListView.as_view(), name="goods-receipt-list"),
    path("receipts/<uuid:pk>/", views.GoodsReceiptDetailView.as_view(), name="goods-receipt-detail"),
    path("receipt-lines/", views.GoodsReceiptLineListView.as_view(), name="goods-receipt-line-list"),
    path("receipt-lines/<uuid:pk>/", views.GoodsReceiptLineDetailView.as_view(), name="goods-receipt-line-detail"),
]
