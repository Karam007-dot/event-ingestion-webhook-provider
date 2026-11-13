from django.urls import path
from .views import WebhookIngestView, health_check_view

urlpatterns = [
    path('ingest/', WebhookIngestView.as_view(), name='webhook-ingest'),
    path('health/', health_check_view, name='health-check'),
]