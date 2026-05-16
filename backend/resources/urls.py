from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import (
    MissionTaskViewSet,
    ServiceConfigViewSet,
    ServiceTokenViewSet,
    TaskConversationViewSet,
)
from .views import (
    DashboardView,
    ToolsIndexView,
    oauth_action,
    resource_create_page,
    resource_list_page,
    x_callback,
)

router = DefaultRouter()
router.register("service-configs", ServiceConfigViewSet, basename="service-config")
router.register("service-tokens", ServiceTokenViewSet, basename="service-token")
router.register("mission-tasks", MissionTaskViewSet, basename="mission-task")
router.register(
    "task-conversations", TaskConversationViewSet, basename="task-conversation"
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("tools/", ToolsIndexView.as_view(), name="tools-index"),
    path("x-callback/", x_callback, name="x-callback"),
    path("x/callback", x_callback, name="x-callback-alt"),
    path("resources/<slug:resource_name>/", resource_list_page, name="resource-list"),
    path(
        "resources/<slug:resource_name>/create/",
        resource_create_page,
        name="resource-create",
    ),
    path("oauth/<slug:connector_id>/<slug:action>", oauth_action, name="oauth-action"),
    path("api/", include(router.urls)),
]
