from __future__ import annotations

from rest_framework import serializers

from .models import MissionTask, ServiceConfig, ServiceToken, TaskConversation


class ServiceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceConfig
        fields = "__all__"


class ServiceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceToken
        fields = "__all__"


class MissionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionTask
        fields = "__all__"


class TaskConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskConversation
        fields = "__all__"
