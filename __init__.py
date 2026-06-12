"""The BatteryHealth integration."""

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "batteryhealth"
PLATFORMS = ["sensor"]
SERVICE_RESET_HISTORY = "reset_history"
ATTR_ENTRY_ID = "entry_id"

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the BatteryHealth integration."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data.setdefault("runtimes", {})

    if not hass.services.has_service(DOMAIN, SERVICE_RESET_HISTORY):

        async def _async_handle_reset_history(call) -> None:
            entry_id = call.data.get(ATTR_ENTRY_ID)
            runtimes = hass.data.get(DOMAIN, {}).get("runtimes", {})

            if entry_id:
                runtime = runtimes.get(entry_id)
                if runtime is None:
                    _LOGGER.warning(
                        "[BatteryHealth] reset_history: no runtime found for entry_id '%s'",
                        entry_id,
                    )
                    return
                runtime.reset_history()
                return

            for runtime in runtimes.values():
                runtime.reset_history()

        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_HISTORY,
            _async_handle_reset_history,
            schema=vol.Schema({vol.Optional(ATTR_ENTRY_ID): str}),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BatteryHealth from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).get("runtimes", {}).pop(entry.entry_id, None)
    return unload_ok