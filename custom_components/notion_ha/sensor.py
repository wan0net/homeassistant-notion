"""Notion kanban sensor — outputs Todoist-compatible JSON for kanban Lovelace cards."""
from __future__ import annotations

import json
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    async_add_entities([NotionKanbanSensor(coordinator, entry)])


class NotionKanbanSensor(CoordinatorEntity[NotionTodoCoordinator], SensorEntity):
    """Sensor that exposes Notion todos in Todoist kanban card format.

    The state is the count of active (non-completed) items.
    The attributes contain 'sections' and 'items' matching the schema
    expected by todoist-kanban-card and power-todoist-card.
    """

    _attr_icon = "mdi:format-list-checks"

    def __init__(
        self, coordinator: NotionTodoCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_kanban"
        self._attr_name = f"{entry.title} Kanban"

    @property
    def native_value(self) -> int:
        """Return count of active items."""
        if not self.coordinator.data:
            return 0
        return sum(
            1
            for item in self.coordinator.data["items"]
            if not item["checked"]
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return Todoist-compatible kanban structure."""
        if not self.coordinator.data:
            return {"sections": [], "items": []}

        data = self.coordinator.data
        sections = data["sections"]
        items = [
            {
                "id": item["id"],
                "content": item["content"],
                "section_id": item["status"].lower().replace(" ", "_"),
                "checked": 1 if item["checked"] else 0,
                "due": {"date": item["due_date"]} if item["due_date"] else None,
            }
            for item in data["items"]
            if not item["checked"]  # hide completed from kanban view
        ]

        return {
            "sections": sections,
            "items": items,
            # project stub so cards that expect it don't error
            "project": {"id": self._entry.entry_id, "name": self._entry.title},
        }
