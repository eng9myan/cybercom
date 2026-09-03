"""CyMed Pharmacy Compounding viewsets."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    CompoundingFormulation,
    CompoundingIngredient,
    CompoundingOrder,
    CompoundingStep,
    IngredientLot,
    QATest,
)
from .serializers import (
    CompoundingFormulationSerializer,
    CompoundingIngredientSerializer,
    CompoundingOrderSerializer,
    CompoundingStepSerializer,
    IngredientLotSerializer,
    QATestSerializer,
)


class CompoundingFormulationViewSet(viewsets.ModelViewSet):
    queryset = CompoundingFormulation.objects.all()
    serializer_class = CompoundingFormulationSerializer


class CompoundingIngredientViewSet(viewsets.ModelViewSet):
    queryset = CompoundingIngredient.objects.all()
    serializer_class = CompoundingIngredientSerializer


class CompoundingOrderViewSet(viewsets.ModelViewSet):
    queryset = CompoundingOrder.objects.all()
    serializer_class = CompoundingOrderSerializer

    @action(detail=False, methods=["post"], url_path="create-order")
    def create_order(self, request):
        order = services.create_order(**request.data)
        return Response(CompoundingOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        order = services.verify_order(order_id=pk, **request.data)
        return Response(CompoundingOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="record-step")
    def record_step(self, request, pk=None):
        step = services.record_step(order_id=pk, **request.data)
        return Response(CompoundingStepSerializer(step).data)

    @action(detail=True, methods=["post"], url_path="record-qa")
    def record_qa(self, request, pk=None):
        qa = services.record_qa(order_id=pk, **request.data)
        return Response(QATestSerializer(qa).data)

    @action(detail=True, methods=["post"], url_path="release")
    def release(self, request, pk=None):
        order = services.release(order_id=pk, **request.data)
        return Response(CompoundingOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        order = services.reject(order_id=pk, **request.data)
        return Response(CompoundingOrderSerializer(order).data)


class CompoundingStepViewSet(viewsets.ModelViewSet):
    queryset = CompoundingStep.objects.all()
    serializer_class = CompoundingStepSerializer


class IngredientLotViewSet(viewsets.ModelViewSet):
    queryset = IngredientLot.objects.all()
    serializer_class = IngredientLotSerializer


class QATestViewSet(viewsets.ModelViewSet):
    queryset = QATest.objects.all()
    serializer_class = QATestSerializer
