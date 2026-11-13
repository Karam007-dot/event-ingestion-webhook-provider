import json
import requests
from celery import shared_task
from django.conf import settings
from .models import WebhookEvent
from .utils import generate_webhook_signature

@shared_task(bind=True, max_retries=3)
def deliver_webhook_task(self, event_id):
    # Define custom backoff intervals in seconds: 5m (300s), 15m (900s), 45m (2700s)
    backoff_intervals = [300, 900, 2700]
    
    try:
        event = WebhookEvent.objects.get(id=event_id)
        
        # Increment attempt counter
        event.attempts += 1
        event.save(update_fields=['attempts'])

        # Prepare payload bytes for signing
        payload_data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "payload": event.payload
        }
        payload_bytes = json.dumps(payload_data, sort_keys=True).encode('utf-8')

        # Generate HMAC SHA256 signature
        secret_key = getattr(settings, 'WEBHOOK_SECRET_KEY', 'your-secure-shared-secret-key')
        signature = generate_webhook_signature(payload_bytes, secret_key)

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'EventProvider-WebhookDispatcher/1.0',
            'X-Webhook-Signature': f"sha256={signature}",
            'X-Webhook-Event-Id': event.event_id,
        }

        # Send outbound HTTP POST request
        response = requests.post(
            event.target_url,
            data=payload_bytes,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        # Mark success if request succeeds
        event.status = 'SUCCESS'
        event.save(update_fields=['status', 'updated_at'])

    except (WebhookEvent.DoesNotExist, requests.RequestException) as exc:
        try:
            event = WebhookEvent.objects.get(id=event_id)
            current_attempt = event.attempts
            
            # Check if we have remaining retries
            if self.request.retries < self.max_retries:
                # Select countdown based on attempt index (fallback to 45m if out of bounds)
                delay = backoff_intervals[min(self.request.retries, len(backoff_intervals) - 1)]
                event.status = 'PENDING' # Keep as pending while waiting for retry
                event.save(update_fields=['status', 'updated_at'])
                
                raise self.retry(exc=exc, countdown=delay)
            else:
                # Max retries exhausted -> Move to FAILED / Dead Letter state
                event.status = 'FAILED'
                event.save(update_fields=['status', 'updated_at'])
        except WebhookEvent.DoesNotExist:
            pass