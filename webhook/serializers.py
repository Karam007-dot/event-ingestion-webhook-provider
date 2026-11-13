from rest_framework import serializers
from .models import WebhookEvent

class WebhookIngestSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=255)
    event_type = serializers.CharField(max_length=100)
    target_url = serializers.URLField()
    payload = serializers.JSONField()

    def validate_event_id(self, value):
        # In strict idempotency design, you can either reject duplicates 
        # or return the existing event status. Let's raise validation error 
        # for duplicate ingestion, or handle it in the view.
        if WebhookEvent.objects.filter(event_id=value).exists():
            raise serializers.ValidationError("An event with this event_id already exists (Idempotency check).")
        return value