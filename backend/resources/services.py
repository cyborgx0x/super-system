from __future__ import annotations

import uuid

from .models import MissionTask, TaskConversation


def ensure_task_conversation(task: MissionTask) -> TaskConversation:
    """Create a conversation record for each mission task."""
    conversation, _ = TaskConversation.objects.get_or_create(
        task=task,
        defaults={
            "state": TaskConversation.State.CREATED,
            "context": {"note": "Provisioned for langgraph orchestration."},
        },
    )
    return conversation


class LangGraphOrchestrator:
    """Thin orchestration facade so connectors can be plugged in as tool-calls later."""

    def start_task(
        self, task: MissionTask, conversation: TaskConversation
    ) -> TaskConversation:
        if not conversation.langgraph_thread_id:
            conversation.langgraph_thread_id = f"lg-{uuid.uuid4()}"

        context = dict(conversation.context or {})
        context.update(
            {
                "task_title": task.title,
                "task_status": task.status,
                "connector_ids": task.meta.get("connector_ids", []),
                "note": "Ready for langgraph execution and connector tool-calling.",
            }
        )
        conversation.context = context
        conversation.state = TaskConversation.State.RUNNING
        conversation.save(
            update_fields=["langgraph_thread_id", "context", "state", "updated_at"]
        )
        return conversation


def provision_langgraph_conversation(task: MissionTask) -> TaskConversation:
    conversation = ensure_task_conversation(task)
    orchestrator = LangGraphOrchestrator()
    return orchestrator.start_task(task, conversation)
