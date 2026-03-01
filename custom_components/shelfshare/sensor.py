from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ShelfShareCoordinator


@dataclass(frozen=True, kw_only=True)
class ShelfShareSensorDescription(SensorEntityDescription):
    value_key: str


SENSOR_DESCRIPTIONS: tuple[ShelfShareSensorDescription, ...] = (
    ShelfShareSensorDescription(
        key="upcoming_events_count",
        name="ShelfShare Upcoming Events",
        icon="mdi:calendar-clock",
        value_key="upcoming_events_count",
    ),
    ShelfShareSensorDescription(
        key="lent_out_active_count",
        name="ShelfShare Lent Out Active",
        icon="mdi:share-variant",
        value_key="lent_out_active_count",
    ),
    ShelfShareSensorDescription(
        key="borrowed_active_count",
        name="ShelfShare Borrowed Active",
        icon="mdi:swap-horizontal",
        value_key="borrowed_active_count",
    ),
    ShelfShareSensorDescription(
        key="collection_games_count",
        name="ShelfShare Collection Games",
        icon="mdi:cards",
        value_key="collection_games_count",
    ),
    ShelfShareSensorDescription(
        key="libraries_count",
        name="ShelfShare Libraries",
        icon="mdi:library-shelves",
        value_key="libraries_count",
    ),
    ShelfShareSensorDescription(
        key="owned_libraries_count",
        name="ShelfShare Owned Libraries",
        icon="mdi:bookshelf",
        value_key="owned_libraries_count",
    ),
    ShelfShareSensorDescription(
        key="unread_notifications_count",
        name="ShelfShare Unread Notifications",
        icon="mdi:bell-badge",
        value_key="unread_notifications_count",
    ),
    ShelfShareSensorDescription(
        key="actionable_notifications_count",
        name="ShelfShare Actionable Notifications",
        icon="mdi:bell-alert",
        value_key="actionable_notifications_count",
    ),
    ShelfShareSensorDescription(
        key="last_sync",
        name="ShelfShare Last Sync",
        icon="mdi:clock-check-outline",
        value_key="generated_at",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ShelfShareSensorDescription(
        key="api_health",
        name="ShelfShare API Health",
        icon="mdi:heart-pulse",
        value_key="api_health",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ShelfShareCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ShelfShareSensor] = [
        ShelfShareSensor(coordinator=coordinator, entry=entry, description=description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class ShelfShareSensor(CoordinatorEntity[ShelfShareCoordinator], SensorEntity):
    entity_description: ShelfShareSensorDescription

    def __init__(
        self,
        coordinator: ShelfShareCoordinator,
        entry: ConfigEntry,
        description: ShelfShareSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}

        if self.entity_description.key == "last_sync":
            return data.get("generated_at")

        if self.entity_description.key == "api_health":
            return self.coordinator.api_health_status

        summary = data.get("summary", {})
        if isinstance(summary, dict):
            return summary.get(self.entity_description.value_key)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        key = self.entity_description.key

        if key == "upcoming_events_count":
            events = data.get("upcoming_events", [])
            if isinstance(events, list):
                return {"events": events}

        if key in {"unread_notifications_count", "actionable_notifications_count"}:
            notifications = data.get("notifications", [])
            if isinstance(notifications, list):
                return {"notifications": notifications}

        if key in {"lent_out_active_count", "borrowed_active_count"}:
            lends = data.get("recent_lends", [])
            if isinstance(lends, list):
                return {"recent_lends": lends}

        if key == "api_health":
            diagnostics = self.coordinator.local_diagnostics()
            return {
                "last_update_success": diagnostics.get("last_update_success"),
                "last_success_at": diagnostics.get("last_success_at"),
                "last_error_at": diagnostics.get("last_error_at"),
                "last_error": diagnostics.get("last_error"),
                "poll_interval_seconds": diagnostics.get("poll_interval_seconds"),
            }

        return None
