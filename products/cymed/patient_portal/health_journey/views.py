from rest_framework import viewsets, permissions, filters
from .models import (
    HealthTimeline,
    HealthTimelineEvent,
    PatientJourney,
    HealthMilestone,
    CareEpisode,
)
from .serializers import (
    HealthTimelineSerializer,
    HealthTimelineEventSerializer,
    PatientJourneySerializer,
    HealthMilestoneSerializer,
    CareEpisodeSerializer,
)


class HealthTimelineViewSet(viewsets.ModelViewSet):
    serializer_class = HealthTimelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['timeline_name']
    ordering_fields = ['last_updated', 'created_at', 'total_events']
    ordering = ['-last_updated']

    def get_queryset(self):
        qs = HealthTimeline.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get('patient_id')
        account_id = self.request.query_params.get('account_id')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        return qs


class HealthTimelineEventViewSet(viewsets.ModelViewSet):
    serializer_class = HealthTimelineEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'provider_name', 'facility_name']
    ordering_fields = ['event_date', 'event_type', 'created_at']
    ordering = ['-event_date']

    def get_queryset(self):
        qs = HealthTimelineEvent.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get('patient_id')
        account_id = self.request.query_params.get('account_id')
        timeline_id = self.request.query_params.get('timeline_id')
        event_type = self.request.query_params.get('event_type')
        is_pinned = self.request.query_params.get('is_pinned')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if timeline_id:
            qs = qs.filter(timeline_id=timeline_id)
        if event_type:
            qs = qs.filter(event_type=event_type)
        if is_pinned is not None:
            qs = qs.filter(is_pinned=is_pinned.lower() == 'true')
        return qs


class PatientJourneyViewSet(viewsets.ModelViewSet):
    serializer_class = PatientJourneySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['journey_name', 'primary_diagnosis', 'icd11_code']
    ordering_fields = ['start_date', 'status', 'journey_type', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        qs = PatientJourney.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get('patient_id')
        account_id = self.request.query_params.get('account_id')
        status = self.request.query_params.get('status')
        journey_type = self.request.query_params.get('journey_type')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if status:
            qs = qs.filter(status=status)
        if journey_type:
            qs = qs.filter(journey_type=journey_type)
        return qs


class HealthMilestoneViewSet(viewsets.ModelViewSet):
    serializer_class = HealthMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['milestone_date', 'is_achieved', 'milestone_type', 'created_at']
    ordering = ['-milestone_date']

    def get_queryset(self):
        qs = HealthMilestone.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get('patient_id')
        account_id = self.request.query_params.get('account_id')
        journey_id = self.request.query_params.get('journey_id')
        milestone_type = self.request.query_params.get('milestone_type')
        is_achieved = self.request.query_params.get('is_achieved')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if journey_id:
            qs = qs.filter(journey_id=journey_id)
        if milestone_type:
            qs = qs.filter(milestone_type=milestone_type)
        if is_achieved is not None:
            qs = qs.filter(is_achieved=is_achieved.lower() == 'true')
        return qs


class CareEpisodeViewSet(viewsets.ModelViewSet):
    serializer_class = CareEpisodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'facility_name', 'primary_diagnosis', 'icd11_code',
        'attending_physician',
    ]
    ordering_fields = ['admission_date', 'discharge_date', 'episode_type', 'created_at']
    ordering = ['-admission_date']

    def get_queryset(self):
        qs = CareEpisode.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get('patient_id')
        account_id = self.request.query_params.get('account_id')
        journey_id = self.request.query_params.get('journey_id')
        episode_type = self.request.query_params.get('episode_type')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if journey_id:
            qs = qs.filter(journey_id=journey_id)
        if episode_type:
            qs = qs.filter(episode_type=episode_type)
        return qs
