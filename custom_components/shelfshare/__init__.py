from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_DECISION,
    ATTR_ENTRY_ID,
    ATTR_NOTIFICATION_ID,
    ATTR_NOTIFICATION_TYPE,
    ATTR_RELATED_ID,
    DOMAIN,
    PLATFORMS,
    SERVICE_COMPLETE_NOTIFICATION,
    SERVICE_GET_DIAGNOSTICS,
    SERVICE_MARK_NOTIFICATION_READ,
    SERVICE_REFRESH_NOW,
    SERVICE_RUN_NOTIFICATION_ACTION,
)
from .coordinator import ShelfShareCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ShelfShareCoordinator(hass=hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_MARK_NOTIFICATION_READ):
        _register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _resolve_coordinator(hass: HomeAssistant, entry_id: str | None) -> ShelfShareCoordinator:
    entries: dict[str, ShelfShareCoordinator] = hass.data.get(DOMAIN, {})
    if not entries:
        raise HomeAssistantError("No ShelfShare configuration entries loaded")

    if entry_id:
        coordinator = entries.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"ShelfShare entry not found: {entry_id}")
        return coordinator

    return next(iter(entries.values()))


def _register_services(hass: HomeAssistant) -> None:
    async def _get_diagnostics(call: ServiceCall) -> dict[str, Any]:
        coordinator = _resolve_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        return await coordinator.async_get_diagnostics()

    async def _refresh_now(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.async_request_refresh()

    async def _mark_notification_read(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.async_run_action(
            {
                "action": "mark_notification_read",
                "notificationId": call.data[ATTR_NOTIFICATION_ID],
            }
        )
        await coordinator.async_request_refresh()

    async def _complete_notification(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.async_run_action(
            {
                "action": "complete_notification",
                "notificationId": call.data[ATTR_NOTIFICATION_ID],
            }
        )
        await coordinator.async_request_refresh()

    async def _run_notification_action(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get(ATTR_ENTRY_ID))

        payload: dict[str, Any] = {
            "action": "notification_action",
            "decision": call.data.get(ATTR_DECISION, "view"),
            "payload": {
                "notificationId": call.data[ATTR_NOTIFICATION_ID],
                "type": call.data[ATTR_NOTIFICATION_TYPE],
                "relatedId": call.data[ATTR_RELATED_ID],
            },
        }
        await coordinator.async_run_action(payload)
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_NOW,
        _refresh_now,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DIAGNOSTICS,
        _get_diagnostics,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_NOTIFICATION_READ,
        _mark_notification_read,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Required(ATTR_NOTIFICATION_ID): vol.Coerce(int),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_NOTIFICATION,
        _complete_notification,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Required(ATTR_NOTIFICATION_ID): vol.Coerce(int),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_NOTIFICATION_ACTION,
        _run_notification_action,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTRY_ID): cv.string,
                vol.Required(ATTR_NOTIFICATION_ID): vol.Coerce(int),
                vol.Required(ATTR_NOTIFICATION_TYPE): cv.string,
                vol.Required(ATTR_RELATED_ID): cv.string,
                vol.Optional(ATTR_DECISION, default="view"): vol.In(
                    ["accept", "decline", "snooze", "view"]
                ),
            }
        ),
    )
