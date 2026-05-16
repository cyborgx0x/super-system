from __future__ import annotations

from django.contrib import admin

from .models import MissionTask, ServiceConfig, ServiceToken, TaskConversation

admin.site.register(ServiceConfig)
admin.site.register(ServiceToken)
admin.site.register(MissionTask)
admin.site.register(TaskConversation)
