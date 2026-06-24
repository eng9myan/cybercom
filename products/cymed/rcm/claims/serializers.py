from rest_framework import serializers
from .models import Claim, ClaimLine, ClaimSubmission, ClaimResponse, ClaimStatus, ClaimAttachment


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = "__all__"


class ClaimLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimLine
        fields = "__all__"


class ClaimSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimSubmission
        fields = "__all__"


class ClaimResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimResponse
        fields = "__all__"


class ClaimStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimStatus
        fields = "__all__"


class ClaimAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimAttachment
        fields = "__all__"
