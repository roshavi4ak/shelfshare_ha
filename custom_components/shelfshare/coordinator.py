from __future__ import annotations

from datetime import UTC, datetime
from datetime import timedelta
import hashlib
import json
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ACTION_PATH, CONF_API_KEY, CONF_BASE_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DIAGNOSTICS_PATH, DOMAIN, SUMMARY_PATH

_LOGGER = logging.getLogger(__name__)


class ShelfShareCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._base_url = str(entry.data[CONF_BASE_URL]).rstrip("/")
        self._api_key = str(entry.data[CONF_API_KEY])
        self._session = async_get_clientsession(hass)
        self._last_success_at: str | None = None
        self._last_error_at: str | None = None
        self._last_error: str | None = None

        interval_seconds = int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.title}",
            update_interval=timedelta(seconds=max(30, interval_seconds)),
        )

    @property
    def summary_url(self) -> str:
        return f"{self._base_url}{SUMMARY_PATH}"

    @property
    def action_url(self) -> str:
        return f"{self._base_url}{ACTION_PATH}"

    @property
    def diagnostics_url(self) -> str:
        return f"{self._base_url}{DIAGNOSTICS_PATH}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-shelfshare-api-key": self._api_key,
            "Authorization": f"Bearer {self._api_key}",
            "apikey": self._api_key,
        }

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    def _build_notification_action_idempotency_key(
        self, payload: dict[str, Any]
    ) -> str:
        action_payload = payload.get("payload")
        if not isinstance(action_payload, dict):
            return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        material = {
            "entry_id": self.entry.entry_id,
            "action": payload.get("action"),
            "decision": payload.get("decision", "view"),
            "notificationId": action_payload.get("notificationId"),
            "type": action_payload.get("type"),
            "relatedId": action_payload.get("relatedId"),
        }
        serialized = json.dumps(material, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @property
    def api_health_status(self) -> str:
        if self.last_update_success:
            return "ok"

        error_text = (self._last_error or "").lower()
        if "rate limit" in error_text or "429" in error_text:
            return "rate_limited"
        if "invalid shelfshare api key" in error_text or "missing summary_read" in error_text:
            return "auth_error"
        if self._last_error:
            return "degraded"
        return "unknown"

    def local_diagnostics(self) -> dict[str, Any]:
        return {
            "generated_at": self._now_iso(),
            "entry_id": self.entry.entry_id,
            "entry_title": self.entry.title,
            "last_update_success": self.last_update_success,
            "last_success_at": self._last_success_at,
            "last_error_at": self._last_error_at,
            "last_error": self._last_error,
            "api_health": self.api_health_status,
            "poll_interval_seconds": int(
                self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with self._session.get(
                self.summary_url,
                headers=self.headers,
                timeout=20,
            ) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed("Invalid ShelfShare API key")
                if response.status == 403:
                    raise ConfigEntryAuthFailed(
                        "ShelfShare API key is inactive or missing summary_read scope"
                    )
                if response.status >= 400:
                    body = await response.text()
                    raise UpdateFailed(
                        f"Summary endpoint error {response.status}: {body[:200]}"
                    )
                data = await response.json()
                if not isinstance(data, dict):
                    raise UpdateFailed("Unexpected summary payload from ShelfShare")
                self._last_success_at = self._now_iso()
                self._last_error = None
                return data
        except ConfigEntryAuthFailed:
            self._last_error = "Authentication failed"
            self._last_error_at = self._now_iso()
            raise
        except ClientError as err:
            self._last_error = str(err)
            self._last_error_at = self._now_iso()
            raise ConfigEntryNotReady(f"Network error contacting ShelfShare: {err}") from err
        except UpdateFailed:
            self._last_error = "Update failed"
            self._last_error_at = self._now_iso()
            raise
        except Exception as err:  # pragma: no cover
            self._last_error = str(err)
            self._last_error_at = self._now_iso()
            raise UpdateFailed(f"Unexpected ShelfShare update error: {err}") from err

    async def async_run_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            action_name = payload.get("action")
            if action_name == "notification_action" and not payload.get("idempotencyKey"):
                payload = dict(payload)
                payload["idempotencyKey"] = self._build_notification_action_idempotency_key(payload)

            async with self._session.post(
                self.action_url,
                headers=self.headers,
                json=payload,
                timeout=20,
            ) as response:
                body = await response.json(content_type=None)
                if response.status >= 400:
                    error_message = body.get("error") if isinstance(body, dict) else str(body)
                    raise UpdateFailed(
                        f"Action endpoint error {response.status}: {error_message}"
                    )
                if not isinstance(body, dict):
                    return {"success": True, "result": body}
                return body
        except ClientError as err:
            raise UpdateFailed(f"Network error calling ShelfShare action endpoint: {err}") from err

    async def async_get_diagnostics(self) -> dict[str, Any]:
        local = self.local_diagnostics()
        try:
            async with self._session.get(
                self.diagnostics_url,
                headers=self.headers,
                timeout=20,
            ) as response:
                body = await response.json(content_type=None)
                if response.status >= 400:
                    return {
                        "local": local,
                        "server": {
                            "error": body.get("error") if isinstance(body, dict) else str(body),
                            "status_code": response.status,
                        },
                    }
                if not isinstance(body, dict):
                    return {
                        "local": local,
                        "server": {"error": "Unexpected diagnostics payload"},
                    }
                return {
                    "local": local,
                    "server": body,
                }
        except ClientError as err:
            return {
                "local": local,
                "server": {"error": f"Network error: {err}"},
            }
