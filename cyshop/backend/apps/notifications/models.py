from django.db import models
from django.conf import settings
from apps.tenants.models import BaseEntity

class SystemNotification(BaseEntity):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='INFO') # INFO, WARNING, SUCCESS, DANGER
    is_read = models.BooleanField(default=False)
    
    # Ready flags for multi-channel notification routing
    send_email = models.BooleanField(default=False)
    send_push = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"
