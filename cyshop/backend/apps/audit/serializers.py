from rest_framework import serializers
from .models import SystemAuditLog

class SystemAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemAuditLog
        fields = '__all__'
