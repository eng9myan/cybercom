from rest_framework import serializers
from .models import (
    TelemedicineSession,
    TelemedicineDocument,
    TelemedicineChat,
    TelemedicineRating,
)


class TelemedicineDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineDocument
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_at']


class TelemedicineChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineChat
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'sent_at']


class TelemedicineRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineRating
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TelemedicineSessionSerializer(serializers.ModelSerializer):
    documents = TelemedicineDocumentSerializer(many=True, read_only=True)
    chat_messages = TelemedicineChatSerializer(many=True, read_only=True)
    session_rating = TelemedicineRatingSerializer(read_only=True)

    class Meta:
        model = TelemedicineSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TelemedicineSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
