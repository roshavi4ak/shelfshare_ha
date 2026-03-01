from __future__ import annotations

from typing import Any

import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_SCAN_INTERVAL, DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN, SUMMARY_PATH


async def _validate_input(hass, data: dict[str, Any]) -> dict[str, Any]:
    base_url = str(data[CONF_BASE_URL]).rstrip("/")
    api_key = str(data[CONF_API_KEY]).strip()

    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"{base_url}{SUMMARY_PATH}",
            headers={"x-shelfshare-api-key": api_key},
            timeout=20,
        ) as response:
            if response.status in (401, 403):
                raise InvalidAuth
            if response.status >= 400:
                raise CannotConnect
            payload = await response.json(content_type=None)
            if not isinstance(payload, dict) or "summary" not in payload:
                raise InvalidResponse
    except ClientError as err:
        raise CannotConnect from err

    return {
        "title": data.get("name") or DEFAULT_NAME,
        CONF_BASE_URL: base_url,
        CONF_API_KEY: api_key,
    }


class ShelfShareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                str(user_input[CONF_BASE_URL]).rstrip("/").lower()
            )
            self._abort_if_unique_id_configured()

            try:
                info = await _validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pragma: no cover
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input.get("name") or info["title"],
                    data={
                        CONF_BASE_URL: info[CONF_BASE_URL],
                        CONF_API_KEY: info[CONF_API_KEY],
                    },
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional("name", default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return ShelfShareOptionsFlow(entry)


class ShelfShareOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._entry.options.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


class CannotConnect(Exception):
    pass


class InvalidAuth(Exception):
    pass


class InvalidResponse(Exception):
    pass
