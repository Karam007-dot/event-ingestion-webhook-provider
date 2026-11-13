from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import WebhookIngestSerializer
from .models import WebhookEvent
from .tasks import deliver_webhook_task

@api_view(['GET'])
def health_check_view(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return Response({
        "status": "online",
        "database": db_status
    })

class WebhookIngestView(APIView):
    def post(self, request):
        serializer = WebhookIngestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Save audit log entry
            event_obj = WebhookEvent.objects.create(
                event_id=data['event_id'],
                event_type=data['event_type'],
                target_url=data['target_url'],
                payload=data['payload'],
                status='PENDING'
            )
            
            # Instant dispatch to Celery queue (non-blocking)
            deliver_webhook_task.delay(event_obj.id)
            
            return Response(
                {"status": "queued", "event_id": data['event_id']}, 
                status=status.HTTP_202_ACCEPTED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)