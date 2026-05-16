from __future__ import annotations

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ServiceConfig(TimeStampedModel):
    service_name = models.CharField(max_length=120, unique=True)
    service_type = models.CharField(max_length=40, default="external")
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.service_name


class ServiceToken(TimeStampedModel):
    config = models.ForeignKey(
        ServiceConfig, on_delete=models.CASCADE, related_name="tokens"
    )
    token_type = models.CharField(max_length=40, default="bearer")
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.config.service_name}:{self.token_type}"


class MissionTask(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.title


class Resource(TimeStampedModel):
    class Category(models.TextChoices):
        PRODUCT = "product", "Product"
        CHANNEL = "channel", "Channel"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.PRODUCT)
    icon = models.CharField(max_length=10, blank=True)
    icon_class = models.CharField(max_length=30, blank=True)
    links = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return self.name


class Quest(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DONE = "done", "Done"
        LOCKED = "locked", "Locked"

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=10, blank=True)
    icon_class = models.CharField(max_length=30, blank=True)
    reward = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self) -> str:
        return self.title


class AccessService(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    url = models.URLField(blank=True)
    is_external = models.BooleanField(default=False)
    extra_links = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return self.name


class TaskConversation(TimeStampedModel):
    class State(models.TextChoices):
        CREATED = "created", "Created"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        ERROR = "error", "Error"

    task = models.OneToOneField(
        MissionTask, on_delete=models.CASCADE, related_name="conversation"
    )
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    langgraph_thread_id = models.CharField(max_length=255, blank=True)
    state = models.CharField(
        max_length=20, choices=State.choices, default=State.CREATED
    )
    context = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.task_id}:{self.conversation_id}"
