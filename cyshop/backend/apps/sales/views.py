from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import (
    Lead, Opportunity, Activity, Task, Meeting, Quotation, QuotationLine,
    SalesOrder, OrderLine, SalesCommunication
)
from .serializers import (
    LeadSerializer, OpportunitySerializer, ActivitySerializer, TaskSerializer,
    MeetingSerializer, QuotationSerializer, SalesOrderSerializer, SalesCommunicationSerializer
)

class LeadViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LeadSerializer

    def get_queryset(self):
        return Lead.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def convert(self, request, pk=None):
        """Action endpoint to convert a Lead to an Opportunity."""
        lead = self.get_object()
        if lead.status == 'QUALIFIED':
            return Response({"error": "Lead is already qualified"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Update Lead Status
        lead.status = 'QUALIFIED'
        lead.save()

        # 2. Create Opportunity
        opp_name = f"Opp - {lead.company if lead.company else lead.name}"
        opportunity = Opportunity.objects.create(
            tenant_id=request.tenant_id,
            lead=lead,
            name=opp_name,
            stage='QUALIFIED',
            probability=20,
            expected_revenue=lead.expected_revenue,
            owner=lead.owner
        )

        # 3. Log Activity
        Activity.objects.create(
            tenant_id=request.tenant_id,
            lead=lead,
            opportunity=opportunity,
            activity_type='FOLLOW_UP',
            description=f"Converted Lead to Opportunity: {opp_name}",
            is_completed=True
        )

        return Response({
            "message": "Lead successfully converted to Opportunity",
            "opportunity_id": opportunity.id,
            "opportunity_name": opp_name
        }, status=status.HTTP_200_OK)

class OpportunityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        return Opportunity.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

class ActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return Activity.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

class MeetingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MeetingSerializer

    def get_queryset(self):
        return Meeting.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

class QuotationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuotationSerializer

    def get_queryset(self):
        return Quotation.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Action endpoint for Manager Override discount approval."""
        quotation = self.get_object()
        if quotation.status == 'APPROVED':
            return Response({"message": "Quotation is already approved"}, status=status.HTTP_200_OK)

        quotation.status = 'APPROVED'
        quotation.save()

        # Log audit or trace activity
        return Response({
            "message": f"Quotation {quotation.quotation_number} approved via manager override",
            "status": quotation.status
        }, status=status.HTTP_200_OK)

class SalesOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SalesOrderSerializer

    def get_queryset(self):
        return SalesOrder.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)

class SalesCommunicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SalesCommunicationSerializer

    def get_queryset(self):
        return SalesCommunication.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)
