"""Notion todo list entity with full read/write support."""
from __future__ import annotations

from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NotionTodoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NotionTodoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NotionTodoListEntity(coordinator, entry)])


def _notion_status_to_ha(status: str, completed_statuses: list[str]) -> TodoItemStatus:
    if status in completed_statuses:
        return TodoItemStatus.COMPLETED
    return TodoItemStatus.NEEDS_ACTION


class NotionTodoListEntity(CoordinatorEntity[NotionTodoCoordinator], TodoListEntity):
    """HA todo entity backed by a Notion database.

    Supports creating, updating (rename + status), and deleting items.
    All writes are pushed back to Notion immediately.
    """

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(
        self, coordinator: NotionTodoCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_todo"
        self._attr_name = entry.title

    @property
    def todo_items(self) -> list[TodoItem]:
        if not self.coordinator.data:
            return []

        return [
            TodoItem(
                uid=item["id"],
                summary=item["content"],
                status=_notion_status_to_ha(
                    item["status"], self.coordinator.completed_statuses
                ),
                due=item["due_date"],
                url=item["url"],
            )
            for item in self.coordinator.data["items"]
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new item in Notion."""
        await self.coordinator.async_create_item(
            title=item.summary or "",
            status=None,  # defaults to first active status
        )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an existing item — rename and/or change status."""
        updates: dict[str, Any] = {}

        if item.summary is not None:
            updates["Name"] = {
                "title": [{"text": {"content": item.summary}}]
            }

        if item.status is not None:
            prop_type = await self.coordinator._detect_property_type()
            if item.status == TodoItemStatus.COMPLETED:
                target = (
                    self.coordinator.completed_statuses[0]
                    if self.coordinator.completed_statuses
                    else "Done"
                )
            else:
                target = (
                    self.coordinator.active_statuses[0]
                    if self.coordinator.active_statuses
                    else "To Do"
                )
            updates[self.coordinator.status_property] = {
                prop_type: {"name": target}
            }

        if item.due is not None:
            updates["Due"] = {"date": {"start": str(item.due)}}

        if updates:
            await self.coordinator.client.update_page(item.uid, updates)
            await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Archive pages in Notion (soft-delete)."""
        for uid in uids:
            await self.coordinator.async_delete_item(uid)
