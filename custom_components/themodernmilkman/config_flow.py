"""Config flow for The Modern Milkman integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any
from urllib.parse import urlencode

import voluptuous as vol
from homeassistant.components.calendar import CalendarEntityFeature
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CALENDARS,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    CONF_CUSTOMER,
    CONF_USER,
    CONF_FORENAME,
    CONF_SURNAME,
)

from .coordinator import TMMLoginCoordinator

_LOGGER = logging.getLogger(__name__)


async def _get_calendar_entities(hass: HomeAssistant) -> list[str]:
    """Retrieve calendar entities."""
    entity_registry = er.async_get(hass)
    calendar_entities = {}
    for entity_id, entity in entity_registry.entities.items():
        if entity_id.startswith("calendar."):
            calendar_entity = hass.states.get(entity_id)
            if calendar_entity:
                supported_features = calendar_entity.attributes.get(
                    "supported_features", 0
                )

                supports_create_event = (
                    supported_features & CalendarEntityFeature.CREATE_EVENT
                )

                if supports_create_event:
                    calendar_name = entity.original_name or entity_id
                    calendar_entities[entity_id] = calendar_name

    calendar_entities["None"] = "Create a new calendar"
    return calendar_entities


@callback
def async_get_options_flow(config_entry):
    """Async options flow."""
    return TMMFlowHandler(config_entry)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    session = async_get_clientsession(hass)
    coordinator = TMMLoginCoordinator(hass, session, data)

    await coordinator.async_refresh()

    if coordinator.last_exception is not None and data is not None:
        raise InvalidAuth

    print(coordinator.data)
    user = coordinator.data[CONF_CUSTOMER][CONF_USER]

    return {"title": f"{user[CONF_FORENAME]} {user[CONF_SURNAME]}"}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for The Modern Milkman."""

    VERSION = 1

    @callback
    def _entry_exists(self):
        """Check if an entry for this domain already exists."""
        existing_entries = self._async_current_entries()
        return len(existing_entries) > 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if self._entry_exists():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        calendar_entities = await _get_calendar_entities(self.hass)

        user_input = user_input or {}

        STEP_USER_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(
                    CONF_CALENDARS, default=user_input.get(CONF_CALENDARS, [])
                ): cv.multi_select(calendar_entities),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        if user_input:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class TMMFlowHandler(OptionsFlow):
    """The Modern Milkman flow handler."""

    def __init__(self, config_entry) -> None:
        """Init."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""

        return self.async_show_form(
            step_id="init",
            data_schema={},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
