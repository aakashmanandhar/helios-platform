from django.urls import path
from . import views

urlpatterns = [
    path("ltv-rfm/", views.ltv_rfm, name="kpi-ltv-rfm"),
    path("churn-risk/", views.churn_risk, name="kpi-churn-risk"),
    path("marketing-roi/", views.marketing_roi, name="kpi-marketing-roi"),
    path("funnel-conversion/", views.funnel_conversion, name="kpi-funnel-conversion"),
    path("inventory-risk/", views.inventory_risk, name="kpi-inventory-risk"),
]
