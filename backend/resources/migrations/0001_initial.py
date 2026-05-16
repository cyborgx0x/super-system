from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MissionTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("meta", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="ServiceConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("service_name", models.CharField(max_length=120, unique=True)),
                ("service_type", models.CharField(default="external", max_length=40)),
                ("client_id", models.CharField(blank=True, max_length=255)),
                ("client_secret", models.CharField(blank=True, max_length=255)),
                ("settings", models.JSONField(blank=True, default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="TaskConversation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "conversation_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("langgraph_thread_id", models.CharField(blank=True, max_length=255)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("running", "Running"),
                            ("done", "Done"),
                            ("error", "Error"),
                        ],
                        default="created",
                        max_length=20,
                    ),
                ),
                ("context", models.JSONField(blank=True, default=dict)),
                (
                    "task",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="conversation",
                        to="resources.missiontask",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ServiceToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("token_type", models.CharField(default="bearer", max_length=40)),
                ("access_token", models.TextField(blank=True)),
                ("refresh_token", models.TextField(blank=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="tokens",
                        to="resources.serviceconfig",
                    ),
                ),
            ],
        ),
    ]
