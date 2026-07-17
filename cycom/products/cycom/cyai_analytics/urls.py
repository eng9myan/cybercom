from django.urls import path

from products.cycom.cyai_analytics.views import CyaiUsageAnalyticsView

urlpatterns = [path("summary/", CyaiUsageAnalyticsView.as_view(), name="cyai-analytics-summary")]
