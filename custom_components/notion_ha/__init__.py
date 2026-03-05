"""Notion integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ACTIVE_STATUSES,
    CONF_COMPLETED_STATUSES,
    CONF_DATABASE_ID,
    CONF_STATUS_PROPERTY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import NotionTodoCoordinator
from .notion_client import NotionClient

PLATFORMS = [Platform.SENSOR, Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = NotionClient(session, entry.data[CONF_API_KEY])

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = NotionTodoCoordinator(
        hass=hass,
        client=client,
        database_id=entry.data[CONF_DATABASE_ID],
        status_property=entry.data[CONF_STATUS_PROPERTY],
        active_statuses=entry.data[CONF_ACTIVE_STATUSES],
        completed_statuses=entry.data[CONF_COMPLETED_STATUSES],
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
