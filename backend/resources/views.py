from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

from connectors.base import OAuthSessionData
from connectors.registry import get_connector
from connectors.session_store import SESSION_TTL_SECONDS, STORE
from django.db import models
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .models import (
    AccessService,
    MissionTask,
    Quest,
    Resource,
    ServiceConfig,
    ServiceToken,
    TaskConversation,
)
from .services import provision_langgraph_conversation

RESOURCE_MODEL_MAP = {
    "service-configs": ServiceConfig,
    "service-tokens": ServiceToken,
    "mission-tasks": MissionTask,
    "task-conversations": TaskConversation,
}

TAB_ORDER = ["focus", "grow", "maintain", "learn"]


class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        missions = MissionTask.objects.order_by("id")
        tabs = {}
        for tab_key in TAB_ORDER:
            tabs[tab_key] = []
        for m in missions:
            tab = (m.meta or {}).get("tab", "focus")
            if tab not in tabs:
                tabs[tab] = []
            tabs[tab].append(m)
        ctx["tabs"] = tabs
        ctx["products"] = Resource.objects.filter(category="product").order_by("id")
        ctx["channels"] = Resource.objects.filter(category="channel").order_by("id")
        ctx["quests"] = Quest.objects.order_by("id")
        ctx["access_services"] = AccessService.objects.order_by("id")
        return ctx


class ToolsIndexView(TemplateView):
    template_name = "dashboard/tools_index.html"


def x_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET.get("code", "").strip()
    state = request.GET.get("state", "").strip()
    error = request.GET.get("error", "").strip()

    if error:
        return render(
            request,
            "oauth/x_callback.html",
            {"error": error, "detail": request.GET.get("error_description", "")},
        )

    if not code or not state:
        return render(
            request,
            "oauth/x_callback.html",
            {
                "error": "missing_params",
                "detail": "code or state missing from callback URL.",
            },
        )

    connector = get_connector("x")
    if not connector:
        return render(
            request,
            "oauth/x_callback.html",
            {"error": "connector_not_found", "detail": "X connector not registered."},
        )

    session = STORE.pop_by_state("x", state)
    if not session:
        return render(
            request,
            "oauth/x_callback.html",
            {
                "error": "invalid_session",
                "detail": "OAuth session not found or expired.",
            },
        )

    payload = session.payload
    session_data = OAuthSessionData(
        state=state,
        verifier=str(payload.get("verifier", "")),
        client_id=str(payload.get("client_id", "")),
        client_secret=str(payload.get("client_secret", "")),
        redirect_uri=str(payload.get("redirect_uri", "")),
        scope=str(payload.get("scope", "")),
    )

    try:
        token_payload = connector.exchange_code(session_data, code)
    except HTTPError as err:
        try:
            detail = json.loads(err.read().decode())
        except Exception:
            detail = str(err)
        return render(
            request,
            "oauth/x_callback.html",
            {"error": "exchange_failed", "detail": detail},
        )
    except Exception as err:
        return render(
            request,
            "oauth/x_callback.html",
            {"error": "exchange_failed", "detail": str(err)},
        )

    config, _ = ServiceConfig.objects.get_or_create(
        service_name="x",
        defaults={"service_type": "oauth"},
    )

    expires_at = None
    if token_payload.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=int(token_payload["expires_in"])
        )

    ServiceToken.objects.update_or_create(
        config=config,
        token_type=token_payload.get("token_type", "bearer"),
        defaults={
            "access_token": token_payload.get("access_token", ""),
            "refresh_token": token_payload.get("refresh_token", ""),
            "expires_at": expires_at,
        },
    )

    return render(
        request,
        "oauth/x_callback.html",
        {"success": True, "scope": token_payload.get("scope", "")},
    )


def resource_list_page(request: HttpRequest, resource_name: str) -> HttpResponse:
    model = RESOURCE_MODEL_MAP.get(resource_name)
    if not model:
        return JsonResponse({"error": "resource_not_found"}, status=404)

    objects = model.objects.order_by("-updated_at")[:50]
    columns = [f.name for f in model._meta.fields]

    return render(
        request,
        "resources/list.html",
        {
            "resource_name": resource_name,
            "resource_model": model._meta.verbose_name_plural.title(),
            "columns": columns,
            "rows": objects,
            "api_path": f"/api/{resource_name}/",
        },
    )


@csrf_exempt
def resource_create_page(request: HttpRequest, resource_name: str) -> HttpResponse:
    model = RESOURCE_MODEL_MAP.get(resource_name)
    if not model:
        return JsonResponse({"error": "resource_not_found"}, status=404)

    if request.method == "GET":
        fields = [
            f
            for f in model._meta.fields
            if not getattr(f, "auto_created", False)
            and f.name not in {"id", "created_at", "updated_at"}
        ]
        return render(
            request,
            "resources/create.html",
            {
                "resource_name": resource_name,
                "resource_model": model._meta.verbose_name.title(),
                "fields": fields,
            },
        )

    payload = {}
    for field in model._meta.fields:
        if getattr(field, "auto_created", False) or field.name in {
            "id",
            "created_at",
            "updated_at",
        }:
            continue

        raw = request.POST.get(field.name, "")
        if field.is_relation and field.many_to_one:
            if raw:
                rel_model = field.remote_field.model
                payload[field.name] = get_object_or_404(rel_model, pk=raw)
            continue

        if isinstance(field, models.JSONField):
            payload[field.name] = json.loads(raw) if raw else {}
            continue
        if isinstance(field, models.BooleanField):
            payload[field.name] = raw.lower() in {"1", "true", "yes", "on"}
            continue

        payload[field.name] = raw

    obj = model.objects.create(**payload)
    if isinstance(obj, MissionTask):
        provision_langgraph_conversation(obj)

    return JsonResponse({"ok": True, "id": obj.pk})


@csrf_exempt
def oauth_action(request: HttpRequest, connector_id: str, action: str) -> JsonResponse:
    connector = get_connector(connector_id)
    if not connector:
        return JsonResponse(
            {
                "error": "connector_not_found",
                "detail": f"Unsupported connector: {connector_id}",
            },
            status=404,
        )

    if request.method == "GET":
        return _oauth_get(request, connector, action)
    if request.method == "POST":
        return _oauth_post(request, connector_id, connector, action)
    return JsonResponse({"error": "method_not_allowed"}, status=405)


def _oauth_get(request: HttpRequest, connector, action: str) -> JsonResponse:
    if action not in {"users-me", "verify"}:
        return JsonResponse(
            {"error": "not_found", "detail": f"Unsupported action: {action}"},
            status=404,
        )

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JsonResponse(
            {"error": "invalid_request", "detail": "Missing Bearer token."}, status=400
        )

    access_token = auth.removeprefix("Bearer ").strip()
    try:
        payload = connector.verify_access_token(access_token)
        return JsonResponse(payload, status=200)
    except HTTPError as err:
        return _http_error_to_json(err)
    except Exception as err:  # noqa: BLE001
        return JsonResponse({"error": "upstream_error", "detail": str(err)}, status=502)


def _oauth_post(
    request: HttpRequest, connector_id: str, connector, action: str
) -> JsonResponse:
    if action == "session":
        return _create_oauth_session(request, connector_id, connector)
    if action == "exchange":
        return _exchange_oauth_code(request, connector_id, connector)
    if action == "token":
        return _legacy_token_exchange(request, connector)
    return JsonResponse(
        {"error": "not_found", "detail": f"Unsupported action: {action}"}, status=404
    )


def _create_oauth_session(
    request: HttpRequest, connector_id: str, connector
) -> JsonResponse:
    client_id = request.POST.get("client_id", "").strip()
    client_secret = request.POST.get("client_secret", "").strip()
    redirect_uri = request.POST.get("redirect_uri", "").strip()
    scope = request.POST.get("scope", "users.read tweet.read").strip()

    if not client_id:
        try:
            cfg = ServiceConfig.objects.get(service_name=connector_id)
            client_id = cfg.client_id
            client_secret = client_secret or cfg.client_secret
        except ServiceConfig.DoesNotExist:
            pass

    if not client_id or not redirect_uri:
        return JsonResponse(
            {
                "error": "invalid_request",
                "detail": "Missing client_id or redirect_uri.",
            },
            status=400,
        )

    session_data = connector.new_session_data(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
    )
    session_id = STORE.create(
        connector_id,
        {
            "state": session_data.state,
            "verifier": session_data.verifier,
            "client_id": session_data.client_id,
            "client_secret": session_data.client_secret,
            "redirect_uri": session_data.redirect_uri,
            "scope": session_data.scope,
        },
    )

    return JsonResponse(
        {
            "session_id": session_id,
            "authorize_url": connector.build_authorize_url(session_data),
            "expires_in": SESSION_TTL_SECONDS,
        }
    )


def _exchange_oauth_code(
    request: HttpRequest, connector_id: str, connector
) -> JsonResponse:
    session_id = request.POST.get("session_id", "").strip()
    code = request.POST.get("code", "").strip()
    state = request.POST.get("state", "").strip()

    if not session_id or not code or not state:
        return JsonResponse(
            {
                "error": "invalid_request",
                "detail": "Missing session_id, code, or state.",
            },
            status=400,
        )

    session = STORE.get(session_id)
    if not session:
        return JsonResponse(
            {
                "error": "invalid_session",
                "detail": "OAuth session not found or expired.",
            },
            status=400,
        )
    if session.connector_id != connector_id:
        return JsonResponse(
            {"error": "invalid_session", "detail": "Connector mismatch for session."},
            status=400,
        )

    expected_state = str(session.payload.get("state", ""))
    if expected_state != state:
        return JsonResponse(
            {"error": "invalid_state", "detail": "OAuth state mismatch."}, status=400
        )

    payload = session.payload
    session_data = OAuthSessionData(
        state=str(payload.get("state", "")),
        verifier=str(payload.get("verifier", "")),
        client_id=str(payload.get("client_id", "")),
        client_secret=str(payload.get("client_secret", "")),
        redirect_uri=str(payload.get("redirect_uri", "")),
        scope=str(payload.get("scope", "")),
    )

    try:
        token_payload = connector.exchange_code(session_data, code)
        STORE.pop(session_id)
        return JsonResponse(token_payload)
    except HTTPError as err:
        return _http_error_to_json(err)
    except NotImplementedError as err:
        return JsonResponse(
            {"error": "not_implemented", "detail": str(err)}, status=501
        )
    except Exception as err:  # noqa: BLE001
        return JsonResponse({"error": "upstream_error", "detail": str(err)}, status=502)


def _legacy_token_exchange(request: HttpRequest, connector) -> JsonResponse:
    code = request.POST.get("code", "").strip()
    verifier = request.POST.get("code_verifier", "").strip()
    client_id = request.POST.get("client_id", "").strip()
    client_secret = request.POST.get("client_secret", "").strip()
    redirect_uri = request.POST.get("redirect_uri", "").strip()

    if not code or not verifier or not client_id or not redirect_uri:
        return JsonResponse(
            {"error": "invalid_request", "detail": "Missing required fields."},
            status=400,
        )

    session_data = OAuthSessionData(
        state="",
        verifier=verifier,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=request.POST.get("scope", ""),
    )
    try:
        return JsonResponse(connector.exchange_code(session_data, code))
    except HTTPError as err:
        return _http_error_to_json(err)
    except Exception as err:  # noqa: BLE001
        return JsonResponse({"error": "upstream_error", "detail": str(err)}, status=502)


def _http_error_to_json(err: HTTPError) -> JsonResponse:
    try:
        body = err.read().decode("utf-8")
        payload = json.loads(body)
    except Exception:
        payload = {"error": "upstream_error", "detail": str(err)}
    return JsonResponse(payload, status=err.code)
