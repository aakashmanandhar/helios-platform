from django.urls import path
from . import views

urlpatterns = [
    path("score/<str:customer_id>/", views.score_customer, name="churn-score"),
    path("top-risk/", views.top_risk, name="churn-top-risk"),
]
