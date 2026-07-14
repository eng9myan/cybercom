from rest_framework import serializers
from .models import SystemNotification

class SystemNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemNotification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'send_email', 'send_push', 'send_whatsapp', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        tenant_id = self.context['request'].tenant_id
        validated_data['tenant_id'] = tenant_id
        return super().create(validated_data)
