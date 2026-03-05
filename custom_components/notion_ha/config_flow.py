"""Config flow for Notion integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    NumberSelector,
    NumberSelectorConfig,
)

from .const import (
    CONF_ACTIVE_STATUSES,
    CONF_COMPLETED_STATUSES,
    CONF_DATABASE_ID,
    CONF_STATUS_PROPERTY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STATUS_PROPERTY_TYPES,
)
from .notion_client import NotionClient, parse_database_id

_LOGGER = logging.getLogger(__name__)


class NotionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Notion."""

    VERSION = 1

    def __init__(self) -> None:
        self._api_key: str = ""
        self._database_id: str = ""
        self._db_meta: dict = {}
        self._client: NotionClient | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            session = async_get_clientsession(self.hass)
            client = NotionClient(session, api_key)

            try:
                valid = await client.validate_api_key()
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                if not valid:
                    errors[CONF_API_KEY] = "invalid_auth"
                else:
                    self._api_key = api_key
                    self._client = client
                    return await self.async_step_database()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
        )

    async def async_step_database(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        errors: dict[str, str] = {}

        if user_input is not None:
            db_id = parse_database_id(user_input[CONF_DATABASE_ID])
            try:
                db = await self._client.get_database(db_id)  # type: ignore[union-attr]
            except aiohttp.ClientResponseError as err:
                if err.status == 404:
                    errors[CONF_DATABASE_ID] = "database_not_found"
                elif err.status == 401:
                    errors[CONF_DATABASE_ID] = "database_not_shared"
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                self._database_id = db_id
                self._db_meta = db
                return await self.async_step_status()

        return self.async_show_form(
            step_id="database",
            data_schema=vol.Schema({
                vol.Required(CONF_DATABASE_ID): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
            }),
            errors=errors,
        )

    async def async_step_status(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Let the user pick which property represents status/columns."""
        errors: dict[str, str] = {}

        # Find select/status properties in the schema
        status_props = {
            name: prop
            for name, prop in self._db_meta.get("properties", {}).items()
            if prop.get("type") in STATUS_PROPERTY_TYPES
        }

        if not status_props:
            return self.async_abort(reason="no_status_property")

        if user_input is not None:
            status_prop_name = user_input[CONF_STATUS_PROPERTY]
            prop = status_props[status_prop_name]
            prop_type = prop.get("type")

            # Extract options from the property schema
            if prop_type == "select":
                all_options = [
                    o["name"] for o in prop.get("select", {}).get("options", [])
                ]
            else:  # status
                all_options = [
                    o["name"] for o in prop.get("status", {}).get("options", [])
                ]

            active = user_input.get(CONF_ACTIVE_STATUSES, [])
            completed = user_input.get(CONF_COMPLETED_STATUSES, [])

            if not active:
                errors[CONF_ACTIVE_STATUSES] = "required"
            elif not completed:
                errors[CONF_COMPLETED_STATUSES] = "required"
            else:
                db_title = self._get_db_title()
                await self.async_set_unique_id(self._database_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=db_title,
                    data={
                        CONF_API_KEY: self._api_key,
                        CONF_DATABASE_ID: self._database_id,
                        CONF_STATUS_PROPERTY: status_prop_name,
                        CONF_ACTIVE_STATUSES: active,
                        CONF_COMPLETED_STATUSES: completed,
                    },
                )

        # Build schema dynamically from database properties
        prop_names = list(status_props.keys())
        default_prop = next(
            (n for n in ("Status", "status") if n in prop_names), prop_names[0]
        )
        prop = status_props[default_prop]
        prop_type = prop.get("type")
        if prop_type == "select":
            all_options = [
                o["name"] for o in prop.get("select", {}).get("options", [])
            ]
        else:
            all_options = [
                o["name"] for o in prop.get("status", {}).get("options", [])
            ]

        schema = vol.Schema(
            {
                vol.Required(CONF_STATUS_PROPERTY, default=default_prop): SelectSelector(
                    SelectSelectorConfig(
                        options=prop_names,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_ACTIVE_STATUSES): SelectSelector(
                    SelectSelectorConfig(
                        options=all_options,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(CONF_COMPLETED_STATUSES): SelectSelector(
                    SelectSelectorConfig(
                        options=all_options,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="status",
            data_schema=schema,
            errors=errors,
        )

    def _get_db_title(self) -> str:
        parts = self._db_meta.get("title", [])
        return "".join(p.get("plain_text", "") for p in parts) or "Notion"

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return NotionOptionsFlow(entry)


class NotionOptionsFlow(OptionsFlow):
    """Handle options (scan interval)."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(min=60, max=3600, step=60, unit_of_measurement="s")
                    ),
                }
            ),
        )
