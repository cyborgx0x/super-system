from __future__ import annotations

from rest_framework import viewsets

from .models import MissionTask, ServiceConfig, ServiceToken, TaskConversation
from .serializers import (
    MissionTaskSerializer,
    ServiceConfigSerializer,
    ServiceTokenSerializer,
    TaskConversationSerializer,
)
from .services import provision_langgraph_conversation


class ServiceConfigViewSet(viewsets.ModelViewSet):
    queryset = ServiceConfig.objects.order_by("-updated_at")
    serializer_class = ServiceConfigSerializer


class ServiceTokenViewSet(viewsets.ModelViewSet):
    queryset = ServiceToken.objects.select_related("config").order_by("-updated_at")
    serializer_class = ServiceTokenSerializer


class MissionTaskViewSet(viewsets.ModelViewSet):
    queryset = MissionTask.objects.order_by("-updated_at")
    serializer_class = MissionTaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()
        provision_langgraph_conversation(task)


class TaskConversationViewSet(viewsets.ModelViewSet):
    queryset = TaskConversation.objects.select_related("task").order_by("-updated_at")
    serializer_class = TaskConversationSerializer
