from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/kpi/", include("kpi.urls")),
    path("api/assistant/", include("assistant.urls")),
    path("api/churn/", include("churn.urls")),
]
